"""置信度融合与轻量校准。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional

from intent_recognizer.config import CONFIDENCE_WEIGHTS

try:
    from scipy.optimize import minimize_scalar
except Exception:  # pragma: no cover
    minimize_scalar = None


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _safe_logit(prob: float, eps: float = 1e-6) -> float:
    p = min(max(prob, eps), 1.0 - eps)
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _compute_ece(probs: List[float], labels: List[float], n_bins: int = 10) -> float:
    if not probs or len(probs) != len(labels):
        return 0.0
    total = len(probs)
    ece = 0.0
    for idx in range(n_bins):
        left = idx / n_bins
        right = (idx + 1) / n_bins
        bucket = [i for i, p in enumerate(probs) if (left <= p < right) or (idx == n_bins - 1 and left <= p <= right)]
        if not bucket:
            continue
        acc = sum(labels[i] for i in bucket) / len(bucket)
        conf = sum(probs[i] for i in bucket) / len(bucket)
        ece += abs(acc - conf) * (len(bucket) / total)
    return ece


@dataclass
class ConfidenceSignals:
    """用于融合的多源证据。"""

    model_confidence: float = 0.5
    self_consistency: float = 0.5
    rule_model_agreement: float = 0.5
    cue_density_prior: float = 0.5
    cross_modal_support: float = 0.0
    historical_accuracy: float = 0.7
    context_consistency: float = 0.5


class ConfidenceCalibrator:
    """轻量置信度校准器，支持动态温度。"""

    def __init__(self, temperature: float = 1.0) -> None:
        self.temperature = max(0.1, float(temperature))
        self.temperature_map = {
            "high_risk": 0.3,
            "medium_risk": 0.5,
            "low_risk": 0.8,
            "text_only": 0.5,
            "multimodal": 0.4,
        }

    @staticmethod
    def _weight(name: str) -> float:
        return float(CONFIDENCE_WEIGHTS.get(name, 0.0))

    @staticmethod
    def _logit_scale(prob: float, temperature: float) -> float:
        prob = _clip01(prob)
        if prob in {0.0, 1.0}:
            return prob
        return _clip01(_sigmoid(_safe_logit(prob) / max(0.1, float(temperature))))

    def fuse(self, signals: ConfidenceSignals) -> float:
        raw = (
            self._weight("model_confidence") * _clip01(signals.model_confidence)
            + self._weight("self_consistency") * _clip01(signals.self_consistency)
            + self._weight("rule_model_agreement") * _clip01(signals.rule_model_agreement)
            + self._weight("cue_density_prior") * _clip01(signals.cue_density_prior)
            + self._weight("cross_modal_support") * _clip01(signals.cross_modal_support)
            + self._weight("historical_accuracy") * _clip01(signals.historical_accuracy)
            + self._weight("context_consistency") * _clip01(signals.context_consistency)
        )
        fused = _clip01(raw)
        if fused > 0.5:
            fused = 0.5 + (fused - 0.5) * 1.2
        else:
            fused = 0.5 - (0.5 - fused) * 1.2
        return _clip01(fused)

    def apply_temperature(self, prob: float) -> float:
        return self._logit_scale(prob, self.temperature)

    def get_dynamic_temperature(self, context: Optional[dict] = None) -> float:
        if not context:
            return self.temperature
        temp = self.temperature
        risk_level = context.get("risk_level", "medium")
        if risk_level == "high":
            temp = self.temperature_map.get("high_risk", temp)
        elif risk_level == "low":
            temp = self.temperature_map.get("low_risk", temp)
        else:
            temp = self.temperature_map.get("medium_risk", temp)
        input_type = context.get("input_type", "text_only")
        if input_type == "multimodal":
            temp = min(temp, self.temperature_map.get("multimodal", temp))
        user_risk_preference = context.get("user_risk_preference", "medium")
        if user_risk_preference == "risk_averse":
            temp *= 0.8
        elif user_risk_preference == "risk_seeking":
            temp *= 1.2
        return max(0.1, min(5.0, temp))

    def calibrate(self, signals: ConfidenceSignals, context: Optional[dict] = None) -> float:
        fused = self.fuse(signals)
        dynamic_temp = self.get_dynamic_temperature(context)
        return self._logit_scale(fused, dynamic_temp)

    def fit_temperature(self, probs: Iterable[float], labels: Iterable[bool], n_bins: int = 10) -> float:
        probs_list: List[float] = [_clip01(float(p)) for p in probs]
        labels_list: List[float] = [1.0 if bool(v) else 0.0 for v in labels]
        if not probs_list or len(probs_list) != len(labels_list):
            return self.temperature

        def objective(temp: float) -> float:
            calibrated = [self._logit_scale(p, temp) for p in probs_list]
            return _compute_ece(calibrated, labels_list, n_bins=n_bins)

        if minimize_scalar is not None:
            result = minimize_scalar(objective, bounds=(0.1, 5.0), method="bounded")
            if result.success:
                self.temperature = float(result.x)
                return self.temperature

        best_t = self.temperature
        best_loss = float("inf")
        for t in [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0]:
            loss = objective(t)
            if loss < best_loss:
                best_loss = loss
                best_t = t
        self.temperature = best_t
        return self.temperature
