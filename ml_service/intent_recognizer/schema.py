"""意图识别模块核心数据结构。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisDepth(str, Enum):
    NONE = "NONE"
    SHALLOW = "SHALLOW"
    DEEP = "DEEP"


class RiskStage(str, Enum):
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"
    S6 = "S6"


class RecommendedAction(str, Enum):
    EDUCATE = "educate"
    VERIFY = "verify"
    WARN = "warn"
    BLOCK = "block"
    REPORT = "report"


class IntentType(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"
    RISK_CHECK = "RISK_CHECK"
    EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"
    SAFETY_GUIDANCE = "SAFETY_GUIDANCE"


@dataclass
class BaseCue:
    text: str
    cue_type: str
    source: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TextCue(BaseCue):
    source: str = "text"


@dataclass
class ImageCue(BaseCue):
    source: str = "image"


@dataclass
class AudioCue(BaseCue):
    source: str = "audio"


@dataclass
class CueSet:
    text_cues: List[TextCue] = field(default_factory=list)
    image_cues: List[ImageCue] = field(default_factory=list)
    audio_cues: List[AudioCue] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    cross_modal_matches: List[str] = field(default_factory=list)
    tactic_tags: List[str] = field(default_factory=list)
    inferred_scam_type: str = "OTHER_UNKNOWN"
    cue_density_score: float = 0.0

    def total_cue_count(self) -> int:
        return len(self.text_cues) + len(self.image_cues) + len(self.audio_cues)

    def all_cues(self) -> List[BaseCue]:
        return [*self.text_cues, *self.image_cues, *self.audio_cues]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntentInput:
    text: str
    session_id: str = "default"
    user_profile: Dict[str, Any] = field(default_factory=dict)
    image_ocr_text: str = ""
    image_caption: str = ""
    image_path: str = ""
    audio_text: str = ""
    audio_path: str = ""
    video_path: str = ""
    audio_deepfake_score: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def profile_id(self) -> str:
        return str(self.user_profile.get("id") or "") if isinstance(self.user_profile, dict) else ""


@dataclass
class IntentResult:
    original_query: str
    cues: CueSet
    analysis_depth: str
    is_fraud_relevant: bool
    intent: str
    coarse_category: str
    risk_stage: str
    risk_stage_urgency: str
    recommended_action: str
    primary_signals: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    clarifying_questions: List[str] = field(default_factory=list)
    target_collections: List[str] = field(default_factory=list)
    needs_graph_lookup: bool = False
    needs_second_hop: bool = False
    short_circuit: bool = False
    short_circuit_response: str = ""
    confidence: float = 0.0
    safety_rule_triggered: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    has_image: bool = False
    has_audio: bool = False
    session_risk_ceiling: str = RiskStage.S0.value
    accumulated_cue_count: int = 0
    reasoning: str = ""
    llm_used: bool = False
    llm_fallback_reason: str = ""  # 多模态降级时记录原因，便于 trace 排查

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_routing_result(self) -> Dict[str, Any]:
        """向旧接口风格做兼容转换。"""
        return {
            "intent": self.intent,
            "is_fraud_relevant": self.is_fraud_relevant,
            "coarse_category": self.coarse_category,
            "risk_stage": self.risk_stage,
            "recommended_action": self.recommended_action,
            "target_collections": list(self.target_collections),
            "needs_graph_lookup": self.needs_graph_lookup,
            "needs_second_hop": self.needs_second_hop,
            "short_circuit": self.short_circuit,
            "short_circuit_response": self.short_circuit_response,
            "confidence": self.confidence,
        }

