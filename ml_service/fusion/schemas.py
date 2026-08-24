"""融合层结构化数据定义。"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class UserProfile:
    user_id: str
    # 基础信息
    age_group: str = "unknown"
    gender: str = "unknown"
    occupation: str = ""
    education: str = "unknown"
    marital_status: str = "unknown"
    # 金融特征
    income_level: str = "unknown"
    investment_preference: str = "unknown"
    credit_card_frequency: str = "unknown"
    online_shopping_frequency: str = "unknown"
    # 行为特征
    device_usage: str = "unknown"
    social_platform_preference: str = "unknown"
    online_time_distribution: str = "unknown"
    # 风险特征
    financial_literacy: str = "medium"
    risk_preference: str = "moderate"
    risk_cognition_level: str = "medium"
    anti_fraud_knowledge: str = "medium"
    historical_fraud_victims: bool = False
    # 其他
    guardian_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.created_at is not None:
            payload["created_at"] = self.created_at.isoformat()
        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at.isoformat()
        return payload


@dataclass
class RiskEvent:
    user_id: str
    session_id: str = ""
    risk_stage: str = "S0"
    scam_type: str = "OTHER_UNKNOWN"
    risk_score: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.created_at is not None:
            payload["created_at"] = self.created_at.isoformat()
        return payload


@dataclass
class UserBehaviorPattern:
    user_id: str
    total_sessions: int = 0
    high_risk_count: int = 0
    most_common_scam_type: str = "OTHER_UNKNOWN"
    avg_risk_score: float = 0.0
    risk_trend: str = "stable"
    last_high_risk_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.last_high_risk_at is not None:
            payload["last_high_risk_at"] = self.last_high_risk_at.isoformat()
        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at.isoformat()
        return payload


@dataclass
class UserDeviceProfile:
    user_id: str
    device_id: str
    device_type: str = "unknown"
    os_version: str = "unknown"
    app_version: str = "unknown"
    last_used_at: Optional[datetime] = None
    security_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.last_used_at is not None:
            payload["last_used_at"] = self.last_used_at.isoformat()
        return payload


@dataclass
class UserBehaviorEvent:
    user_id: str
    event_type: str
    event_data: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.created_at is not None:
            payload["created_at"] = self.created_at.isoformat()
        return payload


# ------------------------------------------------------------------ #
# 亮点2 — 跨模态一致性报告
# ------------------------------------------------------------------ #
@dataclass
class ConsistencyReport:
    consistency_score: float = 1.0
    contradictions: List[str] = field(default_factory=list)
    anomaly_flags: List[str] = field(default_factory=list)
    modality_scores: Dict[str, float] = field(default_factory=dict)
    needs_clarification: bool = False
    active_modalities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConsistencyReport":
        return cls(
            consistency_score=float(d.get("consistency_score", 1.0)),
            contradictions=list(d.get("contradictions", [])),
            anomaly_flags=list(d.get("anomaly_flags", [])),
            modality_scores=dict(d.get("modality_scores", {})),
            needs_clarification=bool(d.get("needs_clarification", False)),
            active_modalities=list(d.get("active_modalities", [])),
        )


# ------------------------------------------------------------------ #
# 亮点4 — 自我反思结果
# ------------------------------------------------------------------ #
@dataclass
class ReflectionResult:
    adjustment: str = "maintain"          # maintain / escalate / deescalate / clarify
    score_delta: float = 0.0
    false_positive_risk: float = 0.0
    false_negative_risk: float = 0.0
    clarifying_questions: List[str] = field(default_factory=list)
    reflection_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------------ #
# 主输出结构（含亮点1/2/4 新增字段）
# ------------------------------------------------------------------ #
@dataclass
class MlPredictResult:
    risk_score: float
    scam_type: str
    confidence: float
    risk_action: str
    tags: List[str] = field(default_factory=list)
    report: str = ""
    chat_response: str = ""
    user_risk_multiplier: float = 1.0
    user_risk_reason: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 亮点1 — Conformal Prediction
    risk_interval: Dict[str, Any] = field(default_factory=dict)
    risk_prediction_set: List[str] = field(default_factory=list)
    # 亮点2 — 跨模态一致性
    consistency_score: float = 1.0
    consistency_report: Dict[str, Any] = field(default_factory=dict)
    # 亮点4 — 自我反思
    reflection_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "riskScore": self.risk_score,
            "scam_type": self.scam_type,
            "scamType": self.scam_type,
            "confidence": self.confidence,
            "risk_action": self.risk_action,
            "riskAction": self.risk_action,
            "tags": list(self.tags),
            "report": self.report,
            "chat_response": self.chat_response,
            "chatResponse": self.chat_response,
            "user_risk_multiplier": self.user_risk_multiplier,
            "userRiskMultiplier": self.user_risk_multiplier,
            "user_risk_reason": self.user_risk_reason,
            "userRiskReason": self.user_risk_reason,
            "citations": list(self.citations),
            "metadata": dict(self.metadata),
            # 亮点1
            "risk_interval": dict(self.risk_interval),
            "riskInterval": dict(self.risk_interval),
            "risk_prediction_set": list(self.risk_prediction_set),
            "riskPredictionSet": list(self.risk_prediction_set),
            # 亮点2
            "consistency_score": self.consistency_score,
            "consistencyScore": self.consistency_score,
            "consistency_report": dict(self.consistency_report),
            # 亮点4
            "reflection_note": self.reflection_note,
            "reflectionNote": self.reflection_note,
        }
