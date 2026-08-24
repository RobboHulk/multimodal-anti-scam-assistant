"""memory stores 增强能力测试。"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from fusion.memory.postgres_store import PostgresLongTermStore
from fusion.memory.redis_store import RedisMemoryStore
from fusion.schemas import UserBehaviorEvent, UserDeviceProfile
from intent_recognizer import IntentInput, IntentResult
from intent_recognizer.schema import CueSet


class MemoryStoresTestCase(unittest.TestCase):
    def test_redis_cache_profile_roundtrip_in_fallback_mode(self) -> None:
        store = RedisMemoryStore(redis_url="redis://127.0.0.1:0/0")
        profile = {"user_id": "u1", "age_group": "elderly", "risk_preference": "risk_averse"}
        store.cache_user_profile("u1", profile)
        self.assertEqual(store.get_cached_user_profile("u1"), profile)

    def test_postgres_behavior_event_analysis_in_fallback_mode(self) -> None:
        redis_store = RedisMemoryStore(redis_url="redis://127.0.0.1:0/0")
        store = PostgresLongTermStore(dsn="postgresql://invalid", redis_store=redis_store)
        store.record_behavior_event(
            UserBehaviorEvent(
                user_id="u2",
                event_type="session_end",
                event_data={"query": "点击链接输入验证码"},
                risk_score=0.82,
                created_at=datetime.now(UTC),
            )
        )
        events = store.get_behavior_events("u2", limit=10)
        self.assertEqual(len(events), 1)
        analysis = store.analyze_user_behavior_timeline("u2", days=30)
        self.assertIn("timeline_analysis", analysis)
        patterns = store.identify_behavior_patterns("u2")
        self.assertIn("pattern", patterns)

    def test_postgres_device_profile_roundtrip_in_fallback_mode(self) -> None:
        store = PostgresLongTermStore(dsn="postgresql://invalid")
        device = UserDeviceProfile(
            user_id="u3",
            device_id="dev-1",
            device_type="android",
            os_version="14",
            app_version="1.0.0",
        )
        store.upsert_device_profile(device)
        profiles = store.get_device_profiles("u3")
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].device_id, "dev-1")

    def test_sync_to_long_term_uses_user_id_from_session_meta(self) -> None:
        redis_store = RedisMemoryStore(redis_url="redis://127.0.0.1:0/0")
        postgres_store = PostgresLongTermStore(dsn="postgresql://invalid", redis_store=redis_store)
        redis_store.cache_user_profile("u4", {"user_id": "u4", "age_group": "young"})
        redis_store.update_session(
            "sync-session",
            IntentInput(text="帮我看看这是不是诈骗", session_id="sync-session", user_profile={"id": "u4"}),
            IntentResult(
                original_query="帮我看看这是不是诈骗",
                cues=CueSet(),
                analysis_depth="SHALLOW",
                is_fraud_relevant=True,
                intent="risk_check",
                coarse_category="OTHER_UNKNOWN",
                risk_stage="S1",
                risk_stage_urgency="low",
                recommended_action="VERIFY",
                confidence=0.6,
                reasoning="test",
                target_collections=["knowledge_base"],
            ),
        )

        self.assertTrue(redis_store.sync_to_long_term("sync-session", postgres_store))
        profile = postgres_store.get_user_profile("u4")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user_id, "u4")


if __name__ == "__main__":
    unittest.main()
