"""渐进式深度门控。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from intent_recognizer.config import DEFAULT_DEEP_THRESHOLD, DEFAULT_NONE_THRESHOLD, GREETING_PATTERNS
from intent_recognizer.schema import AnalysisDepth, CueSet, IntentInput
from intent_recognizer.safety_rules import SafetyDecision, heuristic_risk_stage

try:
    from sklearn.metrics import precision_recall_curve
except Exception:  # pragma: no cover
    precision_recall_curve = None


@dataclass
class DepthGateDecision:
    analysis_depth: str
    score: float
    reasons: List[str] = field(default_factory=list)


class DepthGate:
    """根据线索强度判断后续分析深度。"""

    def __init__(
        self,
        *,
        none_threshold: float = DEFAULT_NONE_THRESHOLD,
        deep_threshold: float = DEFAULT_DEEP_THRESHOLD,
    ) -> None:
        self.none_threshold = none_threshold
        self.deep_threshold = deep_threshold
        self.decision_factor_weights = {
            "cue_density": 1.0,
            "cross_modal": 1.0,
            "risk_stage": 1.5,
            "session_risk": 0.7,
            "deepfake": 1.2,
            "task_complexity": 0.8,
            "user_risk_preference": 0.5,
            "historical_accuracy": 0.6,
        }
        self.adaptive_thresholds = {
            "high_risk": {"none": 0.0, "deep": 2.0},
            "medium_risk": {"none": 0.0, "deep": 2.5},
            "low_risk": {"none": 0.0, "deep": 3.0},
            "complex_task": {"none": 0.0, "deep": 2.0},
            "simple_task": {"none": 0.0, "deep": 3.5},
        }
        self.threshold_adjustment_history: List[Dict[str, Any]] = []
        self.model_params = {
            "learning_rate": 0.01,
            "momentum": 0.9,
            "batch_size": 32,
            "epochs": 10,
        }
        self.adjustment_count = 0

    def score(
        self,
        intent_input: IntentInput,
        cues: CueSet,
        *,
        session_risk_ceiling: str = "S0",
        session_memory=None,
    ) -> tuple[float, List[str]]:
        query = intent_input.text.strip().lower()
        if query and any(query == pattern for pattern in GREETING_PATTERNS):
            return 0.0, ["识别为闲聊问候"]

        stage = heuristic_risk_stage(intent_input, cues)
        score = 0.0
        reasons: List[str] = []
        cue_density_score = cues.cue_density_score
        score += self.decision_factor_weights["cue_density"] * cue_density_score
        reasons.append(f"线索密度={cue_density_score}")
        if cues.cross_modal_matches:
            score += self.decision_factor_weights["cross_modal"] * 1.0
            reasons.append("存在跨模态印证")
        if stage in {"S3", "S4", "S5", "S6"}:
            score += self.decision_factor_weights["risk_stage"] * 1.5
            reasons.append(f"启发式阶段={stage}")
        elif stage in {"S1", "S2"}:
            score += self.decision_factor_weights["risk_stage"] * 0.5
            reasons.append(f"启发式阶段={stage}")
        if session_risk_ceiling in {"S3", "S4", "S5", "S6"}:
            score += self.decision_factor_weights["session_risk"] * 0.7
            reasons.append(f"会话风险基线={session_risk_ceiling}")
        if intent_input.audio_deepfake_score and intent_input.audio_deepfake_score >= 0.8:
            score += self.decision_factor_weights["deepfake"] * 1.2
            reasons.append("音频疑似伪造")

        task_complexity = self._estimate_task_complexity(intent_input, cues)
        score += self.decision_factor_weights["task_complexity"] * task_complexity
        reasons.append(f"任务复杂度={task_complexity:.2f}")
        user_risk_preference = self._get_user_risk_preference(session_memory)
        score += self.decision_factor_weights["user_risk_preference"] * user_risk_preference
        reasons.append(f"用户风险偏好={user_risk_preference:.2f}")
        historical_accuracy = self._get_historical_accuracy(session_memory)
        score += self.decision_factor_weights["historical_accuracy"] * historical_accuracy
        reasons.append(f"历史准确率={historical_accuracy:.2f}")
        return round(score, 2), reasons

    def _estimate_task_complexity(self, intent_input: IntentInput, cues: CueSet) -> float:
        complexity = 0.0
        if len(intent_input.text) > 100:
            complexity += 0.5
        elif len(intent_input.text) > 50:
            complexity += 0.3
        if intent_input.image_path or intent_input.audio_path or intent_input.video_path:
            complexity += 0.5
        if cues.total_cue_count() > 5:
            complexity += 0.3
        elif cues.total_cue_count() > 2:
            complexity += 0.1
        if cues.cross_modal_matches:
            complexity += 0.2
        return min(complexity, 1.0)

    def _get_user_risk_preference(self, session_memory) -> float:
        if session_memory and hasattr(session_memory, "user_profile") and session_memory.user_profile:
            risk_preference = getattr(session_memory.user_profile, "risk_preference", "medium")
            if risk_preference == "risk_averse":
                return 0.8
            if risk_preference == "risk_seeking":
                return 0.3
        return 0.5

    def _get_historical_accuracy(self, session_memory) -> float:
        if session_memory and hasattr(session_memory, "historical_accuracy"):
            return min(max(float(session_memory.historical_accuracy), 0.0), 1.0)
        return 0.7

    def decide(
        self,
        intent_input: IntentInput,
        cues: CueSet,
        *,
        safety_decision: Optional[SafetyDecision] = None,
        session_risk_ceiling: str = "S0",
        session_memory=None,
    ) -> DepthGateDecision:
        if safety_decision is not None:
            return DepthGateDecision(
                analysis_depth=AnalysisDepth.DEEP.value,
                score=10.0,
                reasons=[f"触发硬规则: {safety_decision.rule_name}"],
            )

        score, reasons = self.score(
            intent_input,
            cues,
            session_risk_ceiling=session_risk_ceiling,
            session_memory=session_memory,
        )
        none_threshold, deep_threshold = self.predict_thresholds(
            intent_input,
            cues,
            session_risk_ceiling=session_risk_ceiling,
            session_memory=session_memory,
        )
        if score <= none_threshold:
            return DepthGateDecision(AnalysisDepth.NONE.value, score, reasons + [f"NONE阈值: {none_threshold:.2f}"])
        if score >= deep_threshold:
            return DepthGateDecision(AnalysisDepth.DEEP.value, score, reasons + [f"DEEP阈值: {deep_threshold:.2f}"])
        return DepthGateDecision(AnalysisDepth.SHALLOW.value, score, reasons + [f"阈值范围: {none_threshold:.2f}-{deep_threshold:.2f}"])

    def get_adaptive_thresholds(
        self,
        intent_input: IntentInput,
        cues: CueSet,
        session_risk_ceiling: str,
        session_memory=None,
    ) -> tuple[float, float]:
        none_threshold = self.none_threshold
        deep_threshold = self.deep_threshold
        stage = heuristic_risk_stage(intent_input, cues)
        if stage in {"S3", "S4", "S5", "S6"}:
            config = self.adaptive_thresholds["high_risk"]
        elif stage in {"S1", "S2"}:
            config = self.adaptive_thresholds["medium_risk"]
        else:
            config = self.adaptive_thresholds["low_risk"]
        none_threshold = config["none"]
        deep_threshold = config["deep"]

        task_complexity = self._estimate_task_complexity(intent_input, cues)
        if task_complexity > 0.7:
            deep_threshold = min(deep_threshold, self.adaptive_thresholds["complex_task"]["deep"])
        elif task_complexity < 0.3:
            deep_threshold = max(deep_threshold, self.adaptive_thresholds["simple_task"]["deep"])

        user_risk_preference = self._get_user_risk_preference(session_memory)
        if user_risk_preference > 0.7:
            deep_threshold *= 0.8
        elif user_risk_preference < 0.3:
            deep_threshold *= 1.2
        deep_threshold = max(deep_threshold, none_threshold + 0.5)
        return none_threshold, deep_threshold

    def predict_thresholds(
        self,
        intent_input: IntentInput,
        cues: CueSet,
        session_risk_ceiling: str = "S0",
        session_memory=None,
    ) -> tuple[float, float]:
        none_threshold, deep_threshold = self.get_adaptive_thresholds(
            intent_input,
            cues,
            session_risk_ceiling,
            session_memory,
        )
        if self.threshold_adjustment_history:
            recent_adjustments = self.threshold_adjustment_history[-5:]
            none_adjustment_trend = sum(item.get("none_adjustment", 0.0) for item in recent_adjustments) / len(recent_adjustments)
            deep_adjustment_trend = sum(item.get("deep_adjustment", 0.0) for item in recent_adjustments) / len(recent_adjustments)
            none_threshold += none_adjustment_trend * 0.1
            deep_threshold -= deep_adjustment_trend * 0.1
            deep_threshold = max(deep_threshold, none_threshold + 0.5)
        return none_threshold, deep_threshold

    def adjust_thresholds(self, feedback_data: List[Dict[str, Any]]) -> dict[str, float]:
        if not feedback_data:
            return {"none_threshold": self.none_threshold, "deep_threshold": self.deep_threshold}
        learning_rate = self.model_params["learning_rate"]
        none_error_sum = 0.0
        deep_error_sum = 0.0
        total_samples = len(feedback_data)
        for data in feedback_data:
            predicted_depth = data.get("predicted_depth")
            actual_depth = data.get("actual_depth")
            score = float(data.get("score", 0.0))
            if predicted_depth != actual_depth:
                if actual_depth == AnalysisDepth.NONE.value and score >= self.none_threshold:
                    none_error_sum += score - self.none_threshold
                elif actual_depth == AnalysisDepth.DEEP.value and score < self.deep_threshold:
                    deep_error_sum += self.deep_threshold - score
        if total_samples > 0:
            none_adjustment = (none_error_sum / total_samples) * learning_rate
            deep_adjustment = (deep_error_sum / total_samples) * learning_rate
            self.none_threshold = max(0.0, self.none_threshold + none_adjustment)
            self.deep_threshold = max(self.none_threshold + 0.5, self.deep_threshold - deep_adjustment)
            self.threshold_adjustment_history.append(
                {
                    "timestamp": time.time(),
                    "none_threshold": self.none_threshold,
                    "deep_threshold": self.deep_threshold,
                    "none_adjustment": none_adjustment,
                    "deep_adjustment": deep_adjustment,
                    "sample_count": total_samples,
                }
            )
            self.adjustment_count += 1
        return {"none_threshold": self.none_threshold, "deep_threshold": self.deep_threshold}

    def learn_from_feedback(self, session_id: str, predicted_depth: str, actual_depth: str, score: float) -> None:
        self.adjust_thresholds(
            [
                {
                    "session_id": session_id,
                    "predicted_depth": predicted_depth,
                    "actual_depth": actual_depth,
                    "score": score,
                }
            ]
        )

    def fit_thresholds(
        self,
        scores: Iterable[float],
        none_labels: Iterable[bool],
        deep_labels: Iterable[bool],
        *,
        min_none_precision: float = 0.98,
        min_deep_recall: float = 0.90,
    ) -> dict[str, float]:
        scores_list = [float(x) for x in scores]
        none_list = [bool(x) for x in none_labels]
        deep_list = [bool(x) for x in deep_labels]
        if not scores_list or len(scores_list) != len(none_list) or len(scores_list) != len(deep_list):
            return {"none_threshold": self.none_threshold, "deep_threshold": self.deep_threshold}

        candidate_scores = sorted(set(scores_list))
        if precision_recall_curve is None:
            idx_low = max(0, int(0.1 * (len(candidate_scores) - 1)))
            idx_high = max(0, int(0.7 * (len(candidate_scores) - 1)))
            self.none_threshold = candidate_scores[idx_low]
            self.deep_threshold = candidate_scores[idx_high]
            return {"none_threshold": self.none_threshold, "deep_threshold": self.deep_threshold}

        best_none = self.none_threshold
        best_none_recall = -1.0
        for thr in candidate_scores:
            pred_none = [s < thr for s in scores_list]
            tp = sum(int(p and y) for p, y in zip(pred_none, none_list))
            fp = sum(int(p and not y) for p, y in zip(pred_none, none_list))
            fn = sum(int((not p) and y) for p, y in zip(pred_none, none_list))
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            if precision >= min_none_precision and recall > best_none_recall:
                best_none = thr
                best_none_recall = recall
        if best_none_recall < 0:
            best_none = min(candidate_scores)

        best_deep = self.deep_threshold
        best_deep_precision = -1.0
        for thr in sorted(candidate_scores, reverse=True):
            pred_deep = [s >= thr for s in scores_list]
            tp = sum(int(p and y) for p, y in zip(pred_deep, deep_list))
            fp = sum(int(p and not y) for p, y in zip(pred_deep, deep_list))
            fn = sum(int((not p) and y) for p, y in zip(pred_deep, deep_list))
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            if recall >= min_deep_recall and precision > best_deep_precision:
                best_deep = thr
                best_deep_precision = precision
        if best_deep_precision < 0:
            best_deep = max(candidate_scores)
        self.none_threshold = float(best_none)
        self.deep_threshold = float(max(best_none, best_deep))
        return {"none_threshold": self.none_threshold, "deep_threshold": self.deep_threshold}

    @staticmethod
    def should_escalate_to_deep(*, shallow_confidence: float, predicted_stage: str, has_cross_modal: bool) -> bool:
        if predicted_stage in {"S3", "S4", "S5", "S6"}:
            return True
        if shallow_confidence < 0.7:
            return True
        if has_cross_modal and shallow_confidence < 0.8:
            return True
        return False
