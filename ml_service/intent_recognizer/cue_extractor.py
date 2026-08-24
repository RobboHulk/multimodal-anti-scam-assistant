"""多模态线索抽取器。"""

from __future__ import annotations

from collections import Counter
import re
from typing import Iterable, List

from intent_recognizer.config import DEFAULT_DEEPFAKE_ALERT_THRESHOLD
from intent_recognizer.schema import AudioCue, CueSet, ImageCue, IntentInput, TextCue
from knowledge_graph.scam_type_taxonomy import (
    TACTIC_KEYWORDS,
    TYPE_KEYWORDS,
    infer_scam_type_from_text,
    validate_tactic_tags,
)

try:
    from knowledge_graph.graph_builder.llm_entity_extractor import LLMEntityExtractor
except Exception:  # pragma: no cover
    class _FallbackEntity:
        def __init__(self, text: str, entity_type: str) -> None:
            self.text = text
            self.entity_type = entity_type

        def to_dict(self):
            return {"text": self.text, "type": self.entity_type}

    class LLMEntityExtractor:  # type: ignore[override]
        def __init__(self, use_api: bool = False) -> None:
            self._phone_pattern = re.compile(r"1[3-9]\d{9}")
            self._money_pattern = re.compile(r"\d+(?:\.\d+)?(?:元|万|块|千|百|亿)")
            self._url_pattern = re.compile(r"https?://\S+|www\.\S+")

        def extract(self, text: str):
            entities = []
            for match in self._phone_pattern.finditer(text):
                entities.append(_FallbackEntity(match.group(), "PHONE"))
            for match in self._money_pattern.finditer(text):
                entities.append(_FallbackEntity(match.group(), "MONEY"))
            for match in self._url_pattern.finditer(text):
                entities.append(_FallbackEntity(match.group(), "URL"))
            return entities


class MultiModalCueExtractor:
    """基于规则与轻量实体抽取的多模态线索抽取器。"""

    ENTITY_WEIGHT = {
        "MONEY": 1.2,
        "PHONE": 0.8,
        "BANK_CARD": 1.5,
        "ID_CARD": 1.5,
        "URL": 1.2,
        "APP": 1.0,
        "PLATFORM": 0.8,
    }

    def __init__(self) -> None:
        self.entity_extractor = LLMEntityExtractor(use_api=False)

    def extract(self, intent_input: IntentInput) -> CueSet:
        text_cues = self._extract_text_cues(intent_input.text, source="text")
        image_cues = self._extract_image_cues(intent_input)
        audio_cues = self._extract_audio_cues(intent_input)
        video_cues = self._extract_video_cues(intent_input)

        combined_text = "\n".join(
            part
            for part in [
                intent_input.text,
                intent_input.image_ocr_text,
                intent_input.image_caption,
                intent_input.audio_text,
                *[cue.text for cue in video_cues[:12]],
            ]
            if part
        )
        inferred_scam_type, tactic_tags, _ = infer_scam_type_from_text(combined_text)
        entities = [cue.metadata for cue in text_cues if cue.cue_type == "entity"]
        cross_modal_matches = self._build_cross_modal_matches(text_cues, image_cues, audio_cues, video_cues)
        cue_density_score = round(
            sum(cue.weight for cue in [*text_cues, *image_cues, *audio_cues, *video_cues]) + 0.5 * len(cross_modal_matches),
            2,
        )
        merged_text_cues = [
            *text_cues,
            *[
                TextCue(
                    text=cue.text,
                    cue_type=cue.cue_type,
                    source="video",
                    weight=cue.weight,
                    metadata=cue.metadata,
                )
                for cue in video_cues
            ],
        ]

        return CueSet(
            text_cues=merged_text_cues,
            image_cues=image_cues,
            audio_cues=audio_cues,
            entities=entities,
            cross_modal_matches=cross_modal_matches,
            tactic_tags=validate_tactic_tags(tactic_tags),
            inferred_scam_type=inferred_scam_type,
            cue_density_score=cue_density_score,
        )

    def _extract_text_cues(self, text: str, *, source: str) -> List[TextCue]:
        if not text:
            return []
        cues: List[TextCue] = []
        lowered_text = text.lower()

        for scam_type, keywords in TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in lowered_text:
                    cues.append(
                        TextCue(
                            text=keyword,
                            cue_type="scam_type_keyword",
                            source=source,
                            weight=1.0,
                            metadata={"scam_type": scam_type},
                        )
                    )

        for tactic, keywords in TACTIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in lowered_text:
                    cues.append(
                        TextCue(
                            text=keyword,
                            cue_type="tactic_keyword",
                            source=source,
                            weight=1.1,
                            metadata={"tactic": tactic},
                        )
                    )

        for entity in self.entity_extractor.extract(text):
            cues.append(
                TextCue(
                    text=entity.text,
                    cue_type="entity",
                    source=source,
                    weight=self.ENTITY_WEIGHT.get(entity.entity_type, 0.6),
                    metadata=entity.to_dict(),
                )
            )

        return self._dedupe_text_cues(cues)

    def _extract_image_cues(self, intent_input: IntentInput) -> List[ImageCue]:
        image_text = "\n".join([part for part in [intent_input.image_ocr_text, intent_input.image_caption] if part])
        base_cues = self._extract_text_cues(image_text, source="image")
        return [
            ImageCue(
                text=cue.text,
                cue_type=cue.cue_type,
                source="image",
                weight=cue.weight + 0.2,
                metadata=cue.metadata,
            )
            for cue in base_cues
        ]

    def _extract_audio_cues(self, intent_input: IntentInput) -> List[AudioCue]:
        cues = [
            AudioCue(
                text=cue.text,
                cue_type=cue.cue_type,
                source="audio",
                weight=cue.weight,
                metadata=cue.metadata,
            )
            for cue in self._extract_text_cues(intent_input.audio_text, source="audio")
        ]
        if (
            intent_input.audio_deepfake_score is not None
            and intent_input.audio_deepfake_score >= DEFAULT_DEEPFAKE_ALERT_THRESHOLD
        ):
            cues.append(
                AudioCue(
                    text=f"deepfake:{intent_input.audio_deepfake_score:.2f}",
                    cue_type="deepfake_signal",
                    source="audio",
                    weight=1.8,
                    metadata={"score": intent_input.audio_deepfake_score},
                )
            )
        return cues

    def _extract_video_cues(self, intent_input: IntentInput) -> List[ImageCue]:
        preprocessing = intent_input.context.get("preprocessing", {}) if isinstance(intent_input.context, dict) else {}
        video_info = preprocessing.get("video", {}) if isinstance(preprocessing, dict) else {}
        cues: List[ImageCue] = []
        keyframes = video_info.get("keyframes", []) if isinstance(video_info, dict) else []
        for frame in keyframes[:8]:
            if not isinstance(frame, dict):
                continue
            page_type = str(frame.get("page_type", "")).strip()
            ocr_text = str(frame.get("ocr_text", "")).strip()
            time_pos = frame.get("time", "")
            if page_type:
                cues.append(
                    ImageCue(
                        text=f"video_page:{page_type}",
                        cue_type="video_page_type",
                        source="video",
                        weight=1.1,
                        metadata={"time": time_pos},
                    )
                )
            if ocr_text:
                cues.extend(
                    ImageCue(
                        text=item.text,
                        cue_type=item.cue_type,
                        source="video",
                        weight=item.weight + 0.1,
                        metadata=item.metadata,
                    )
                    for item in self._extract_text_cues(ocr_text, source="video")
                )
        behavior_sequence = video_info.get("behavior_sequence", []) if isinstance(video_info, dict) else []
        for step in behavior_sequence[:10]:
            step_text = str(step).strip()
            if not step_text:
                continue
            cues.append(
                ImageCue(
                    text=step_text,
                    cue_type="video_behavior",
                    source="video",
                    weight=1.0,
                    metadata={},
                )
            )
        return cues

    @staticmethod
    def _dedupe_text_cues(cues: Iterable[TextCue]) -> List[TextCue]:
        seen = set()
        deduped: List[TextCue] = []
        for cue in cues:
            key = (cue.text, cue.cue_type, cue.source)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(cue)
        return deduped

    @staticmethod
    def _build_cross_modal_matches(
        text_cues: List[TextCue],
        image_cues: List[ImageCue],
        audio_cues: List[AudioCue],
        video_cues: List[ImageCue] | None = None,
    ) -> List[str]:
        grouped = Counter()
        for cue in [*text_cues, *image_cues, *audio_cues, *(video_cues or [])]:
            normalized = cue.text.strip().lower()
            if normalized:
                grouped[normalized] += 1
        return [token for token, count in grouped.items() if count >= 2]

