"""会话记忆管理。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from intent_recognizer.schema import IntentInput, IntentResult

STAGE_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}


@dataclass
class SessionMemory:
    session_id: str
    user_id: str = ""
    history: List[str] = field(default_factory=list)
    risk_ceiling: str = "S0"
    accumulated_cue_count: int = 0
    last_category: str = "OTHER_UNKNOWN"

    def summary(self, max_turns: int = 6) -> str:
        recent_history = self.history[-max_turns:]
        if not recent_history:
            return ""
        return "\n".join(recent_history)


class SessionMemoryManager:
    """兼容旧接口的短期记忆管理器，内部优先使用 Redis。"""

    def __init__(self, store: Optional[object] = None) -> None:
        if store is None:
            from fusion.memory.redis_store import RedisMemoryStore

            store = RedisMemoryStore()
        self._store = store

    def get(self, session_id: str) -> SessionMemory:
        return self._store.get_session(session_id)

    def summarize(self, session_id: str) -> str:
        summary = self._store.get_or_create_summary(session_id)
        if summary:
            return summary
        return self.get(session_id).summary()

    def update(self, session_id: str, intent_input: IntentInput, result: IntentResult) -> SessionMemory:
        return self._store.update_session(session_id, intent_input, result)
