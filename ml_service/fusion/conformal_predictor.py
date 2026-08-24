"""
亮点1 — Conformal Prediction 风险置信区间
参考 Conformal Structured Prediction (ICLR 2025)：
  - 用历史风险事件作为校准集，计算非一致性分数分位数
  - 输出结构化预测集（多标签风险等级集合）+ 置信区间
  - 区间宽度 > 30 时标记 needs_human_review
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple

from fusion.schemas import RiskEvent


# 风险等级边界（0-1 分）
_LEVEL_BOUNDS: Dict[str, Tuple[float, float]] = {
    "low":      (0.0,  0.35),
    "medium":   (0.35, 0.65),
    "high":     (0.65, 0.85),
    "critical": (0.85, 1.0),
}

_STAGE_TO_SCORE: Dict[str, float] = {
    "S0": 0.05, "S1": 0.25, "S2": 0.50,
    "S3": 0.72, "S4": 0.92, "S5": 0.88, "S6": 0.90,
}


class ConformalPredictor:
    """
    Split Conformal Prediction for risk score.
    校准集 = 历史 risk_event 表中的判定结果。
    """

    def __init__(self, alpha: float = 0.05) -> None:
        """
        alpha: 错误率上界，coverage = 1 - alpha（默认 95% 覆盖率）
        """
        self.alpha = alpha
        self._nonconformity_scores: List[float] = []
        self._q_alpha: float = 0.20   # 默认分位数（未校准时的保守估计）
        self._calibrated: bool = False

    # ------------------------------------------------------------------ #
    # 校准
    # ------------------------------------------------------------------ #
    def calibrate(self, events: List[RiskEvent]) -> None:
        """
        用历史风险事件校准非一致性分数。
        非一致性分数 = |predicted_score - stage_anchor_score|
        """
        scores: List[float] = []
        for event in events:
            anchor = _STAGE_TO_SCORE.get(event.risk_stage, 50.0)
            predicted = event.risk_score  # 已存储的预测分（0-1）
            scores.append(abs(predicted - anchor))

        if len(scores) < 5:
            # 样本不足，使用保守默认值
            self._q_alpha = 0.20
            self._calibrated = False
            return

        scores.sort()
        # Split Conformal: q = ceil((n+1)(1-alpha)) / n 分位数
        n = len(scores)
        idx = min(math.ceil((n + 1) * (1 - self.alpha)) - 1, n - 1)
        self._q_alpha = scores[idx]
        self._nonconformity_scores = scores
        self._calibrated = True

    # ------------------------------------------------------------------ #
    # 点预测 → 区间
    # ------------------------------------------------------------------ #
    def predict_interval(
        self, risk_score: float
    ) -> Dict[str, Any]:
        """
        返回 {lower, upper, width, coverage, calibrated, needs_human_review}
        """
        lower = max(0.0, round(risk_score - self._q_alpha, 1))
        upper = min(1.0, round(risk_score + self._q_alpha, 4))
        width = round(upper - lower, 4)
        needs_review = width > 0.30
        return {
            "lower": lower,
            "upper": upper,
            "width": width,
            "coverage": round(1.0 - self.alpha, 2),
            "q_alpha": round(self._q_alpha, 2),
            "calibrated": self._calibrated,
            "needs_human_review": needs_review,
        }

    # ------------------------------------------------------------------ #
    # 结构化预测集（Conformal Structured Prediction 核心）
    # ------------------------------------------------------------------ #
    def predict_set(self, risk_score: float) -> Dict[str, Any]:
        """
        返回覆盖真实风险等级的预测集（多标签集合）。
        预测集 = 所有与置信区间有交集的风险等级。
        """
        interval = self.predict_interval(risk_score)
        lower, upper = interval["lower"], interval["upper"]

        prediction_set: Set[str] = set()
        for level, (lb, ub) in _LEVEL_BOUNDS.items():
            # 区间与等级范围有交集
            if lower < ub and upper > lb:
                prediction_set.add(level)

        # 点估计对应的等级
        point_level = self._score_to_level(risk_score)

        return {
            "prediction_set": sorted(prediction_set),
            "point_level": point_level,
            "interval": interval,
            "set_size": len(prediction_set),
            # set_size == 1 表示高置信度单一判定
            "high_confidence": len(prediction_set) == 1,
        }

    # ------------------------------------------------------------------ #
    # 工具方法
    # ------------------------------------------------------------------ #
    @staticmethod
    def _score_to_level(score: float) -> str:
        for level, (lb, ub) in _LEVEL_BOUNDS.items():
            if lb <= score < ub:
                return level
        return "critical" if score >= 0.85 else "low"

    @staticmethod
    def format_for_prompt(interval: Dict[str, Any]) -> str:
        """将置信区间格式化为 Prompt 注入文本。"""
        lower = interval.get("lower", 0)
        upper = interval.get("upper", 100)
        coverage = interval.get("coverage", 0.95)
        calibrated = interval.get("calibrated", False)
        note = "（已用历史数据校准）" if calibrated else "（使用保守默认值）"
        review = "⚠️ 不确定性较高，建议人工复核" if interval.get("needs_human_review") else ""
        return (
            f"风险置信区间: [{lower}, {upper}]，覆盖率 {coverage:.0%}{note}"
            + (f"\n{review}" if review else "")
        )
