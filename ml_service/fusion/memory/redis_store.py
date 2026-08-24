"""Redis 短期记忆存储，含内存降级。"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from intent_recognizer.memory import SessionMemory
from shared.config.llm_config import REDIS_URL

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class RedisMemoryStore:
    SESSION_TTL_SECONDS = 60 * 60 * 2

    def __init__(self, redis_url: str = REDIS_URL) -> None:
        self.redis_url = redis_url
        self._fallback_sessions: Dict[str, SessionMemory] = {}
        self._fallback_states: Dict[str, Any] = {}
        self._fallback_summary: Dict[str, str] = {}
        self._fallback_user_sessions: Dict[str, List[str]] = {}
        self._fallback_user_profiles: Dict[str, Dict[str, Any]] = {}
        self._fallback_behavior_patterns: Dict[str, Dict[str, Any]] = {}
        self._client = None
        self._access_count_key = "cache:access:count"
        self._memory_threshold = 70
        self._memory_warning_threshold = 60
        self._last_memory_check = 0.0
        self._memory_check_interval = 60
        self._performance_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "session_operations": 0,
            "memory_evictions": 0,
            "sync_operations": 0,
            "sync_errors": 0,
        }
        if redis is not None:
            try:
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                self._client = client
            except Exception:
                self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _session_history_key(self, session_id: str) -> str:
        return f"session:{session_id}:history"

    def _session_history_sorted_key(self, session_id: str) -> str:
        return f"session:{session_id}:history:sorted"

    def _session_meta_key(self, session_id: str) -> str:
        return f"session:{session_id}:meta"

    def _session_summary_key(self, session_id: str) -> str:
        return f"session:{session_id}:summary"

    def _state_key(self, session_id: str) -> str:
        return f"session:{session_id}:conversation_state"

    def _user_profile_key(self, user_id: str) -> str:
        return f"user:{user_id}:profile"

    def _user_behavior_pattern_key(self, user_id: str) -> str:
        return f"user:{user_id}:behavior_pattern"

    def _user_sessions_key(self, user_id: str) -> str:
        return f"user:{user_id}:sessions"

    def get_session(self, session_id: str) -> SessionMemory:
        if not self.is_available:
            if session_id not in self._fallback_sessions:
                self._fallback_sessions[session_id] = SessionMemory(session_id=session_id)
            return self._fallback_sessions[session_id]

        assert self._client is not None
        meta = self._client.hgetall(self._session_meta_key(session_id))
        history_key = self._session_history_sorted_key(session_id)
        if self._client.exists(history_key):
            history = self._client.zrange(history_key, 0, -1)
        else:
            history = self._client.lrange(self._session_history_key(session_id), 0, -1)
        return SessionMemory(
            session_id=session_id,
            user_id=meta.get("user_id", ""),
            history=list(history),
            risk_ceiling=meta.get("risk_ceiling", "S0"),
            accumulated_cue_count=int(meta.get("accumulated_cue_count", 0) or 0),
            last_category=meta.get("last_category", "OTHER_UNKNOWN"),
        )

    def update_session(self, session_id: str, intent_input, result) -> SessionMemory:
        self._performance_metrics["session_operations"] += 1
        memory = self.get_session(session_id)
        user_message = f"用户: {intent_input.text}"
        system_message = (
            f"系统判定: stage={result.risk_stage}, action={result.recommended_action}, "
            f"category={result.coarse_category}, signals={','.join(result.primary_signals[:3]) or '无'}"
        )
        memory.history.append(user_message)
        memory.history.append(system_message)
        stage_order = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}
        if stage_order.get(result.risk_stage, 0) >= stage_order.get(memory.risk_ceiling, 0):
            memory.risk_ceiling = result.risk_stage
        memory.accumulated_cue_count += result.cues.total_cue_count()
        memory.last_category = result.coarse_category

        if not self.is_available:
            memory.user_id = getattr(intent_input, "user_id", "") or memory.user_id
            memory.history = memory.history[-20:]
            self._fallback_sessions[session_id] = memory
            user_id = getattr(intent_input, "user_id", "") or ""
            if user_id:
                sessions = self._fallback_user_sessions.setdefault(user_id, [])
                if session_id in sessions:
                    sessions.remove(session_id)
                sessions.append(session_id)
                self._fallback_user_sessions[user_id] = sessions[-50:]
            return memory

        assert self._client is not None
        meta_key = self._session_meta_key(session_id)
        history_sorted_key = self._session_history_sorted_key(session_id)
        history_list_key = self._session_history_key(session_id)
        timestamp = float(self._client.time()[0])
        self._client.hset(
            meta_key,
            mapping={
                "user_id": getattr(intent_input, "user_id", "") or "",
                "risk_ceiling": memory.risk_ceiling,
                "accumulated_cue_count": memory.accumulated_cue_count,
                "last_category": memory.last_category,
            },
        )
        self._client.zadd(history_sorted_key, {user_message: timestamp, system_message: timestamp + 0.001})
        self._client.delete(history_list_key)
        self._client.zremrangebyrank(history_sorted_key, 0, -21)
        self._client.expire(meta_key, self.SESSION_TTL_SECONDS)
        self._client.expire(history_sorted_key, self.SESSION_TTL_SECONDS)

        user_id = getattr(intent_input, "user_id", "") or ""
        if user_id:
            user_sessions_key = self._user_sessions_key(user_id)
            self._client.zadd(user_sessions_key, {session_id: timestamp})
            self._client.expire(user_sessions_key, self.SESSION_TTL_SECONDS * 24)

        self.compress_session_history(session_id)
        return memory

    def get_conversation_state(self, session_id: str):
        from knowledge_graph.rag.conversation_state import ConversationState

        if not self.is_available:
            if session_id not in self._fallback_states:
                self._fallback_states[session_id] = ConversationState(session_id=session_id)
            return self._fallback_states[session_id]

        assert self._client is not None
        raw = self._client.get(self._state_key(session_id))
        if not raw:
            return ConversationState(session_id=session_id)
        return ConversationState(**json.loads(raw))

    def update_conversation_turn(
        self,
        *,
        session_id: str,
        user_query: str,
        assistant_answer: str,
        risk_stage: str,
        category: str,
        rewritten_query: str,
        target_collections: List[str],
        retrieved_evidence: List[Dict[str, Any]],
        clarifying_pending: bool,
    ):
        from knowledge_graph.rag.conversation_state import ConversationState

        state = self.get_conversation_state(session_id)
        state.history.append(f"用户: {user_query}")
        state.history.append(f"助手: {assistant_answer}")
        state.last_risk_stage = risk_stage
        state.last_category = category
        state.last_rewritten_query = rewritten_query
        state.last_target_collections = list(target_collections)
        state.last_retrieved_evidence = list(retrieved_evidence)
        state.clarifying_pending = clarifying_pending
        if len(state.history) > 20:
            state.history = state.history[-20:]

        if not self.is_available:
            self._fallback_states[session_id] = state
            return state

        assert self._client is not None
        key = self._state_key(session_id)
        self._client.set(key, json.dumps(asdict(state), ensure_ascii=False))
        self._client.expire(key, self.SESSION_TTL_SECONDS)
        return state

    def get_or_create_summary(self, session_id: str, summary: str = "") -> str:
        if not self.is_available:
            if summary:
                self._fallback_summary[session_id] = summary
            return self._fallback_summary.get(session_id, "")

        assert self._client is not None
        key = self._session_summary_key(session_id)
        if summary:
            self._client.set(key, summary)
            self._client.expire(key, self.SESSION_TTL_SECONDS)
            return summary
        existing = self._client.get(key)
        return existing or ""

    def compress_session_history(self, session_id: str) -> None:
        if not self.is_available:
            session = self._fallback_sessions.get(session_id)
            if session and len(session.history) > 20:
                session.history = session.history[-20:]
            return

        assert self._client is not None
        history_sorted_key = self._session_history_sorted_key(session_id)
        history_length = self._client.zcard(history_sorted_key)
        if history_length > 30:
            all_messages = self._client.zrange(history_sorted_key, 0, -1, withscores=True)
            important_messages: List[tuple[str, float]] = []
            recent_messages = all_messages[-10:]
            for msg, score in all_messages:
                if "stage=S4" in msg or "stage=S5" in msg or "stage=S6" in msg or "系统判定:" in msg:
                    important_messages.append((msg, score))
            combined_messages: Dict[str, float] = {}
            for msg, score in important_messages + recent_messages:
                combined_messages[msg] = score
            sorted_combined = sorted(combined_messages.items(), key=lambda item: item[1])
            self._client.delete(history_sorted_key)
            for msg, score in sorted_combined:
                self._client.zadd(history_sorted_key, {msg: score})
            self._client.expire(history_sorted_key, self.SESSION_TTL_SECONDS)
        elif history_length > 20:
            self._client.zremrangebyrank(history_sorted_key, 0, -21)

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[str]:
        if not self.is_available:
            return list(reversed(self._fallback_user_sessions.get(user_id, [])))[:limit]

        assert self._client is not None
        user_sessions_key = self._user_sessions_key(user_id)
        return list(self._client.zrevrange(user_sessions_key, 0, limit - 1))

    def cache_user_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        if not self.is_available:
            self._fallback_user_profiles[user_id] = dict(profile)
            return

        assert self._client is not None
        key = self._user_profile_key(user_id)
        self._client.set(key, json.dumps(profile, ensure_ascii=False, default=str))
        self._client.expire(key, 60 * 60 * 24)

    def get_cached_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return self._fallback_user_profiles.get(user_id)

        assert self._client is not None
        key = self._user_profile_key(user_id)
        raw = self._client.get(key)
        if not raw:
            self._performance_metrics["cache_misses"] += 1
            return None
        self._performance_metrics["cache_hits"] += 1
        self._update_access_count(key)
        self._check_memory_usage()
        return json.loads(raw)

    def cache_user_behavior_pattern(self, user_id: str, pattern: Dict[str, Any]) -> None:
        if not self.is_available:
            self._fallback_behavior_patterns[user_id] = dict(pattern)
            return

        assert self._client is not None
        key = self._user_behavior_pattern_key(user_id)
        self._client.set(key, json.dumps(pattern, ensure_ascii=False, default=str))
        self._client.expire(key, 60 * 60 * 12)

    def get_cached_user_behavior_pattern(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return self._fallback_behavior_patterns.get(user_id)

        assert self._client is not None
        key = self._user_behavior_pattern_key(user_id)
        raw = self._client.get(key)
        if not raw:
            self._performance_metrics["cache_misses"] += 1
            return None
        self._performance_metrics["cache_hits"] += 1
        self._update_access_count(key)
        self._check_memory_usage()
        return json.loads(raw)

    def _update_access_count(self, key: str) -> None:
        if not self.is_available:
            return
        assert self._client is not None
        self._client.zincrby(self._access_count_key, 1, key)
        self._client.expire(self._access_count_key, 60 * 60 * 24 * 7)

    def _check_memory_usage(self) -> None:
        if not self.is_available:
            return
        assert self._client is not None
        try:
            current_time = time.time()
            if current_time - self._last_memory_check < self._memory_check_interval:
                return
            self._last_memory_check = current_time
            info = self._client.info("memory")
            used_memory_rss = info.get("used_memory_rss", 0)
            total_system_memory = info.get("total_system_memory", 1) or 1
            memory_usage_percent = (used_memory_rss / total_system_memory) * 100
            if memory_usage_percent > self._memory_threshold:
                self._evict_cache()
                self._performance_metrics["memory_evictions"] += 1
            elif memory_usage_percent > self._memory_warning_threshold:
                self._evict_cache(limit=5)
        except Exception:
            pass

    def _evict_cache(self, limit: int = 10) -> None:
        if not self.is_available:
            return
        assert self._client is not None
        try:
            least_used = self._client.zrange(self._access_count_key, 0, limit - 1)
            for key in least_used:
                self._client.delete(key)
                self._client.zrem(self._access_count_key, key)
        except Exception:
            pass

    def get_performance_metrics(self) -> Dict[str, Any]:
        return dict(self._performance_metrics)

    def reset_performance_metrics(self) -> None:
        self._performance_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "session_operations": 0,
            "memory_evictions": 0,
            "sync_operations": 0,
            "sync_errors": 0,
        }

    def sync_to_long_term(self, session_id: str, postgres_store) -> bool:
        try:
            self._performance_metrics["sync_operations"] += 1
            session = self.get_session(session_id)
            user_id = getattr(session, "user_id", "")
            if user_id:
                profile = self.get_cached_user_profile(user_id)
                if profile:
                    postgres_store.upsert_user_profile(user_id, **profile)
            return True
        except Exception:
            self._performance_metrics["sync_errors"] += 1
            return False

    def batch_sync_to_long_term(self, session_ids: List[str], postgres_store) -> Dict[str, bool]:
        return {session_id: self.sync_to_long_term(session_id, postgres_store) for session_id in session_ids}

    def get_expired_sessions(self, cutoff_time: int) -> List[str]:
        if not self.is_available:
            return []
        assert self._client is not None
        try:
            session_keys = self._client.keys("session:*:meta")
            expired_sessions: List[str] = []
            for key in session_keys:
                session_id = key.split(":")[1]
                ttl = self._client.ttl(key)
                if ttl < 0 or (ttl > 0 and int(time.time()) + ttl < cutoff_time):
                    expired_sessions.append(session_id)
            return expired_sessions
        except Exception:
            return []

    def cleanup_expired_data(self) -> int:
        if not self.is_available:
            return 0
        assert self._client is not None
        try:
            cutoff_time = int(time.time())
            expired_sessions = self.get_expired_sessions(cutoff_time)
            for session_id in expired_sessions:
                keys = [
                    self._session_meta_key(session_id),
                    self._session_summary_key(session_id),
                    self._state_key(session_id),
                    self._session_history_sorted_key(session_id),
                    self._session_history_key(session_id),
                ]
                for key in keys:
                    self._client.delete(key)
            return len(expired_sessions)
        except Exception:
            return 0
