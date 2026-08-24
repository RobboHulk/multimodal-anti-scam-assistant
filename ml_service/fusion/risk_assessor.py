"""个性化风险评估器。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import List, Tuple

from fusion.memory.postgres_store import PostgresLongTermStore
from fusion.schemas import RiskEvent, UserBehaviorPattern, UserProfile


class PersonalizedRiskAssessor:
    """基于画像、历史风险事件与行为模式的个性化风险评估。"""

    def __init__(self, store: PostgresLongTermStore | None = None) -> None:
        self.store = store or PostgresLongTermStore()

    def assess_user_risk_factor(
        self,
        user_id: str,
        *,
        current_scam_type: str = "OTHER_UNKNOWN",
    ) -> Tuple[float, str, List[str]]:
        if not user_id:
            return 1.0, "无特别画像，采用基准打分", []

        profile = self.store.get_user_profile(user_id) or UserProfile(user_id=user_id)
        pattern = self.store.get_behavior_pattern(user_id) or UserBehaviorPattern(user_id=user_id)
        recent_events = self.store.get_recent_risk_events(user_id, limit=10)

        multiplier = 1.0
        reasons: List[str] = []
        factors: List[str] = []

        if profile.age_group == "elderly" and profile.financial_literacy == "low":
            multiplier += 0.25
            reasons.append("老年且金融素养偏低")
            factors.append("vulnerable_group")

        high_risk_count = pattern.high_risk_count
        if high_risk_count > 0:
            delta = 0.15 * min(high_risk_count, 5)
            multiplier += delta
            reasons.append(f"历史高危事件 {high_risk_count} 次")
            factors.append("historical_victim")

        if self._has_recent_high_risk_event(recent_events):
            multiplier += 0.20
            reasons.append("最近 7 天存在高危事件")
            factors.append("recent_high_risk")

        if pattern.risk_trend == "rising":
            multiplier += 0.10
            reasons.append("近期风险趋势上升")
            factors.append("rising_risk_trend")

        if current_scam_type != "OTHER_UNKNOWN" and current_scam_type == pattern.most_common_scam_type:
            multiplier += 0.10
            reasons.append("与历史常见诈骗类型一致")
            factors.append("same_scam_type_recurrence")

        if profile.financial_literacy == "high" and high_risk_count == 0:
            multiplier -= 0.10
            reasons.append("用户金融素养较高且无高危历史")
            factors.append("high_literacy")

        if not reasons:
            reasons.append("无特别画像，采用基准打分")

        multiplier = max(0.8, min(round(multiplier, 2), 2.5))
        return multiplier, "；".join(reasons), factors

    @staticmethod
    def _has_recent_high_risk_event(events: List[RiskEvent]) -> bool:
        threshold = datetime.now(UTC) - timedelta(days=7)
        for event in events:
            if event.risk_stage in {"S3", "S4", "S5", "S6"} and event.created_at and event.created_at >= threshold:
                return True
        return False
