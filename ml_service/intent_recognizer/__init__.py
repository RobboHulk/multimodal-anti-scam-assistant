"""独立的意图识别模块。"""

from .confidence import ConfidenceCalibrator, ConfidenceSignals
from .schema import AnalysisDepth, IntentInput, IntentResult, RecommendedAction, RiskStage

__all__ = [
    "AnalysisDepth",
    "ConfidenceCalibrator",
    "ConfidenceSignals",
    "IntentAnalyzer",
    "IntentInput",
    "IntentResult",
    "RecommendedAction",
    "RiskStage",
]


def __getattr__(name: str):
    if name == "IntentAnalyzer":
        from .analyzer import IntentAnalyzer

        return IntentAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

