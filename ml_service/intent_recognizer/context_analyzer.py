"""上下文理解模块。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fusion.memory.postgres_store import PostgresLongTermStore
from fusion.schemas import RiskEvent, UserBehaviorEvent


class ContextAnalyzer:
    """上下文分析器，用于计算上下文一致性。"""

    def __init__(self, postgres_store: Optional[PostgresLongTermStore] = None):
        self.postgres_store = postgres_store or PostgresLongTermStore()

    def get_context_consistency(self, user_id: str, current_input: str) -> float:
        if not user_id or not current_input:
            return 0.5

        try:
            behavior_events = self.postgres_store.get_behavior_events(user_id, limit=10)
            risk_events = self.postgres_store.get_recent_risk_events(user_id, limit=5)
            consistency_score = 0.5
            if behavior_events:
                consistency_score += self._analyze_behavior_consistency(behavior_events, current_input) * 0.3
            if risk_events:
                consistency_score += self._analyze_risk_consistency(risk_events, current_input) * 0.2
            return min(max(consistency_score, 0.0), 1.0)
        except Exception:
            return 0.5

    def _analyze_behavior_consistency(self, behavior_events: List[UserBehaviorEvent], current_input: str) -> float:
        if not behavior_events:
            return 0.0
        current_keywords = self._extract_keywords(current_input)
        relevant_events = 0
        for event in behavior_events:
            event_keywords = self._extract_keywords(str(event.event_data)) if event.event_data else []
            if set(current_keywords) & set(event_keywords):
                relevant_events += 1
        return relevant_events / len(behavior_events) if behavior_events else 0.0

    def _analyze_risk_consistency(self, risk_events: List[RiskEvent], current_input: str) -> float:
        if not risk_events:
            return 0.0
        current_keywords = self._extract_keywords(current_input)
        relevant_events = 0
        for event in risk_events:
            event_text = f"{event.scam_type} {event.summary}"
            event_keywords = self._extract_keywords(event_text)
            if set(current_keywords) & set(event_keywords):
                relevant_events += 1
        return relevant_events / len(risk_events) if risk_events else 0.0

    def _extract_keywords(self, text: str) -> List[str]:
        if not text:
            return []
        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这",
        }
        normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text).lower()
        words = normalized.split()
        return [word for word in words if word not in stop_words and len(word) > 1]

    def analyze_user_context(self, user_id: str) -> Dict[str, Any]:
        if not user_id:
            return {}
        try:
            return {
                "timeline_analysis": self.postgres_store.analyze_user_behavior_timeline(user_id, days=30),
                "behavior_patterns": self.postgres_store.identify_behavior_patterns(user_id),
                "fraud_patterns": self.postgres_store.identify_fraud_patterns(user_id),
            }
        except Exception:
            return {}
