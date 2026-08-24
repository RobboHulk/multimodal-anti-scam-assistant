"""意图识别模块配置。"""

from __future__ import annotations

from typing import Dict, List

DEFAULT_NONE_THRESHOLD = 0.000000
DEFAULT_DEEP_THRESHOLD = 2.500000
DEFAULT_DEEPFAKE_ALERT_THRESHOLD = 0.8
SHALLOW_TO_DEEP_CONFIDENCE_THRESHOLD = 0.7

CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "model_confidence": 0.24,
    "self_consistency": 0.16,
    "rule_model_agreement": 0.11,
    "cue_density_prior": 0.18,
    "cross_modal_support": 0.10,
    "historical_accuracy": 0.11,
    "context_consistency": 0.10,
}
RULE_MODEL_AGREEMENT_BASE = 0.500000
RULE_MODEL_AGREEMENT_TYPE_BONUS = 0.214286
RULE_MODEL_AGREEMENT_STAGE_BONUS = 0.171429

GREETING_PATTERNS = [
    "你好",
    "您好",
    "在吗",
    "hello",
    "hi",
    "谢谢",
]

STAGE_URGENCY: Dict[str, str] = {
    "S0": "low",
    "S1": "low",
    "S2": "medium",
    "S3": "high",
    "S4": "critical",
    "S5": "high",
    "S6": "critical",
}

STAGE_ACTION: Dict[str, str] = {
    "S0": "educate",
    "S1": "verify",
    "S2": "warn",
    "S3": "block",
    "S4": "block",
    "S5": "report",
    "S6": "report",
}

STAGE_COLLECTIONS: Dict[str, List[str]] = {
    "S0": [],
    "S1": ["fraud_guides"],
    "S2": ["fraud_guides", "prevention_cases"],
    "S3": ["fraud_guides", "emergency_actions", "knowledge_graph"],
    "S4": ["emergency_actions", "knowledge_graph", "law_articles"],
    "S5": ["evidence_collection", "law_articles", "knowledge_graph"],
    "S6": ["law_articles", "knowledge_graph", "prevention_cases"],
}
