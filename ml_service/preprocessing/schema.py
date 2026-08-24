"""多模态预处理统一数据结构。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TextSegment:
    speaker: str = "other"
    timestamp: str = ""
    text: str = ""
    entities: List[str] = field(default_factory=list)
    risk_patterns: List[str] = field(default_factory=list)


@dataclass
class GlobalTextFeatures:
    has_transfer_intent: bool = False
    has_urgency: bool = False
    has_verification_code_request: bool = False


@dataclass
class TextPreprocessResult:
    clean_text: str = ""
    segments: List[TextSegment] = field(default_factory=list)
    global_features: GlobalTextFeatures = field(default_factory=GlobalTextFeatures)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ASRSegment:
    start: float = 0.0
    end: float = 0.0
    speaker: str = "other"
    text: str = ""
    risk_patterns: List[str] = field(default_factory=list)
    is_estimated: bool = False


@dataclass
class AudioFeatures:
    speaker_count: int = 1
    emotion_pressure_score: float = 0.0
    synthetic_voice_score: float = 0.0
    synthetic_voice_available: bool = False
    prosody: Dict[str, float] = field(default_factory=dict)


@dataclass
class AudioPreprocessResult:
    asr_segments: List[ASRSegment] = field(default_factory=list)
    audio_features: AudioFeatures = field(default_factory=AudioFeatures)
    transcript: str = ""
    normalized_audio_path: str = ""
    status: str = "ok"
    source_model: str = ""
    error_code: str = ""
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OCRBlock:
    text: str = ""
    bbox: List[int] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ImagePreprocessResult:
    ocr_text: str = ""
    ocr_blocks: List[OCRBlock] = field(default_factory=list)
    page_type: str = "unknown_page"
    objects: List[str] = field(default_factory=list)
    risk_signals: List[str] = field(default_factory=list)
    enhanced_image_path: str = ""
    status: str = "ok"
    source_model: str = ""
    error_code: str = ""
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KeyFrame:
    time: float = 0.0
    page_type: str = "unknown_page"
    ocr_text: str = ""
    frame_path: str = ""


@dataclass
class VideoPreprocessResult:
    keyframes: List[KeyFrame] = field(default_factory=list)
    audio_summary: Optional[AudioPreprocessResult] = None
    behavior_sequence: List[str] = field(default_factory=list)
    extracted_audio_path: str = ""
    status: str = "ok"
    source_model: str = ""
    error_code: str = ""
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

