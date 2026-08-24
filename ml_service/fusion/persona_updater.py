"""
亮点5 — DEEPER 动态 Persona 画像建模
参考 PersonaMem (arXiv 2025) 多粒度行为信号提炼：
  - 从每次会话结果中提炼多粒度行为信号
  - 更新 financial_literacy / risk_trend / most_common_scam_type 等维度
  - 写回 PostgresLongTermStore.upsert_user_profile()
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from fusion.memory.postgres_store import PostgresLongTermStore
from fusion.schemas import MlPredictResult, RiskEvent


class PersonaUpdater:
    """
    PersonaMem 多粒度动态画像更新器。
    在 MemoryWriter.persist() 中调用，每次高风险会话后更新用户画像。
    """

    # 触发画像更新的最低风险阶段
    UPDATE_THRESHOLD_STAGE = "S2"
    _STAGE_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}

    def __init__(self, store: Optional[PostgresLongTermStore] = None) -> None:
        self.store = store or PostgresLongTermStore()

    def update_after_session(
        self,
        user_id: str,
        fusion_result: MlPredictResult,
        risk_stage: str,
        scam_type: str,
        chat_response_accepted: bool = True,
    ) -> None:
        """
        会话结束后更新用户画像。
        chat_response_accepted: 用户是否接受了系统的风险提示（默认 True）
        """
        if not user_id:
            return
        stage_val = self._STAGE_ORDER.get(risk_stage, 0)
        threshold_val = self._STAGE_ORDER.get(self.UPDATE_THRESHOLD_STAGE, 2)
        if stage_val < threshold_val:
            return

        profile = self.store.get_user_profile(user_id)
        if profile is None:
            return

        updates: Dict[str, Any] = {}

        # 维度1: financial_literacy — 根据用户对警告的反应推断
        updates["financial_literacy"] = self._infer_financial_literacy(
            profile.financial_literacy,
            risk_stage=risk_stage,
            accepted_warning=chat_response_accepted,
            risk_action=fusion_result.risk_action,
        )

        # 维度2: historical_fraud_victims — S4+ 且有 guardian_alert 标记
        if stage_val >= self._STAGE_ORDER["S4"] and "guardian_alert" in fusion_result.tags:
            updates["historical_fraud_victims"] = True

        # 维度3: risk_preference — 根据行为模式推断
        updates["risk_preference"] = self._infer_risk_preference(
            profile.risk_preference, risk_stage=risk_stage
        )

        # 写回画像
        if updates:
            self.store.upsert_user_profile(user_id, **updates)

    def batch_update_from_events(
        self, user_id: str, events: List[RiskEvent]
    ) -> None:
        """
        从历史风险事件批量更新画像（用于冷启动或定期重算）。
        """
        if not user_id or not events:
            return

        profile = self.store.get_user_profile(user_id)
        if profile is None:
            return

        # 统计最近 30 天高危事件
        cutoff = datetime.now(UTC) - timedelta(days=30)
        recent_high = [
            e for e in events
            if self._STAGE_ORDER.get(e.risk_stage, 0) >= 3
            and (e.created_at is None or e.created_at >= cutoff)
        ]

        updates: Dict[str, Any] = {}

        # 高危频率 → 调整 financial_literacy
        if len(recent_high) >= 3 and profile.financial_literacy == "high":
            updates["financial_literacy"] = "medium"
        elif len(recent_high) == 0 and profile.financial_literacy == "low":
            updates["financial_literacy"] = "medium"

        # 曾被骗标记
        victim_events = [
            e for e in events
            if "guardian_alert" in e.tags or self._STAGE_ORDER.get(e.risk_stage, 0) >= 4
        ]
        if victim_events:
            updates["historical_fraud_victims"] = True

        if updates:
            self.store.upsert_user_profile(user_id, **updates)

    # ------------------------------------------------------------------ #
    # 内部推断逻辑
    # ------------------------------------------------------------------ #
    @staticmethod
    def _infer_financial_literacy(
        current: str,
        *,
        risk_stage: str,
        accepted_warning: bool,
        risk_action: str,
    ) -> str:
        """
        根据用户对风险提示的反应推断金融素养。
        - 接受警告 + 低风险阶段 → 维持或提升
        - 拒绝警告 + 高风险阶段 → 降低
        """
        stage_order = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}
        literacy_order = {"low": 0, "medium": 1, "high": 2}
        current_val = literacy_order.get(current, 1)

        stage_val = stage_order.get(risk_stage, 0)
        high_risk = stage_val >= 3
        action_is_block = risk_action.upper() in {"BLOCK", "REPORT"}

        if accepted_warning and not high_risk:
            # 用户接受了低风险提示，素养略微提升
            new_val = min(current_val + 1, 2)
        elif not accepted_warning and high_risk and action_is_block:
            # 用户忽视了高危警告，素养降低
            new_val = max(current_val - 1, 0)
        else:
            new_val = current_val

        reverse = {0: "low", 1: "medium", 2: "high"}
        return reverse[new_val]

    @staticmethod
    def _infer_risk_preference(current: str, *, risk_stage: str) -> str:
        """根据风险阶段推断风险偏好。"""
        stage_order = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}
        stage_val = stage_order.get(risk_stage, 0)
        if stage_val >= 4 and current == "aggressive":
            return "moderate"
        return current
