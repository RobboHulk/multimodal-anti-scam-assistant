"""PostgreSQL 长期记忆存储，含内存降级。"""

from __future__ import annotations

import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from fusion.memory.redis_store import RedisMemoryStore
from fusion.schemas import (
    RiskEvent,
    UserBehaviorEvent,
    UserBehaviorPattern,
    UserDeviceProfile,
    UserProfile,
)
from shared.config.llm_config import POSTGRES_DSN

try:
    import psycopg2
    import psycopg2.extras
except Exception:  # pragma: no cover
    psycopg2 = None


class PostgresLongTermStore:
    def __init__(self, dsn: str = POSTGRES_DSN, redis_store: RedisMemoryStore | None = None) -> None:
        self.dsn = dsn
        self._fallback_profiles: Dict[str, UserProfile] = {}
        self._fallback_events: List[RiskEvent] = []
        self._fallback_patterns: Dict[str, UserBehaviorPattern] = {}
        self._fallback_device_profiles: Dict[str, List[UserDeviceProfile]] = {}
        self._fallback_behavior_events: List[UserBehaviorEvent] = []
        self._conn = None
        self._redis_store = redis_store or RedisMemoryStore()
        self._query_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, float] = {}
        self._cache_ttl = 300
        if psycopg2 is not None:
            try:
                self._conn = psycopg2.connect(dsn)
                self._conn.autocommit = True
            except Exception:
                self._conn = None

    @property
    def is_available(self) -> bool:
        return self._conn is not None

    def _get_cache_key(self, query: str, params: tuple[Any, ...]) -> str:
        return f"query:{hash(query + str(params))}"

    def _check_cache_expiry(self, key: str) -> bool:
        return key not in self._cache_expiry or time.time() > self._cache_expiry[key]

    def _set_cache(self, key: str, value: Any) -> None:
        self._query_cache[key] = value
        self._cache_expiry[key] = time.time() + self._cache_ttl

    def _get_cache(self, key: str) -> Optional[Any]:
        if key not in self._query_cache or self._check_cache_expiry(key):
            self._query_cache.pop(key, None)
            self._cache_expiry.pop(key, None)
            return None
        return self._query_cache[key]

    def _invalidate_cache(self, *keys: str) -> None:
        for key in keys:
            self._query_cache.pop(key, None)
            self._cache_expiry.pop(key, None)

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        if not user_id:
            return None

        cached_profile = self._redis_store.get_cached_user_profile(user_id)
        if cached_profile:
            return UserProfile(**cached_profile)

        if not self.is_available:
            profile = self._fallback_profiles.get(user_id, UserProfile(user_id=user_id))
            self._redis_store.cache_user_profile(user_id, profile.to_dict())
            return profile

        query = "SELECT * FROM user_profile WHERE user_id = %s"
        params = (user_id,)
        cache_key = self._get_cache_key(query, params)
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return UserProfile(**cached_result)

        assert self._conn is not None
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
        profile = UserProfile(**dict(row)) if row else UserProfile(user_id=user_id)
        self._set_cache(cache_key, profile.to_dict())
        self._redis_store.cache_user_profile(user_id, profile.to_dict())
        return profile

    def upsert_user_profile(self, user_id: str, **fields: Any) -> UserProfile:
        profile = self.get_user_profile(user_id) or UserProfile(user_id=user_id)
        for key, value in fields.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        profile.updated_at = datetime.now(UTC)
        if profile.created_at is None:
            profile.created_at = profile.updated_at

        if not self.is_available:
            self._fallback_profiles[user_id] = profile
            self._redis_store.cache_user_profile(user_id, profile.to_dict())
            return profile

        assert self._conn is not None
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profile (user_id, age_group, gender, occupation, education, marital_status,
                    income_level, investment_preference, credit_card_frequency, online_shopping_frequency,
                    device_usage, social_platform_preference, online_time_distribution,
                    financial_literacy, risk_preference, risk_cognition_level, anti_fraud_knowledge,
                    guardian_ids, historical_fraud_victims, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,COALESCE(%s, NOW()),%s)
                ON CONFLICT (user_id) DO UPDATE SET
                    age_group = EXCLUDED.age_group,
                    gender = EXCLUDED.gender,
                    occupation = EXCLUDED.occupation,
                    education = EXCLUDED.education,
                    marital_status = EXCLUDED.marital_status,
                    income_level = EXCLUDED.income_level,
                    investment_preference = EXCLUDED.investment_preference,
                    credit_card_frequency = EXCLUDED.credit_card_frequency,
                    online_shopping_frequency = EXCLUDED.online_shopping_frequency,
                    device_usage = EXCLUDED.device_usage,
                    social_platform_preference = EXCLUDED.social_platform_preference,
                    online_time_distribution = EXCLUDED.online_time_distribution,
                    financial_literacy = EXCLUDED.financial_literacy,
                    risk_preference = EXCLUDED.risk_preference,
                    risk_cognition_level = EXCLUDED.risk_cognition_level,
                    anti_fraud_knowledge = EXCLUDED.anti_fraud_knowledge,
                    guardian_ids = EXCLUDED.guardian_ids,
                    historical_fraud_victims = EXCLUDED.historical_fraud_victims,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    profile.user_id,
                    profile.age_group,
                    profile.gender,
                    profile.occupation,
                    profile.education,
                    profile.marital_status,
                    profile.income_level,
                    profile.investment_preference,
                    profile.credit_card_frequency,
                    profile.online_shopping_frequency,
                    profile.device_usage,
                    profile.social_platform_preference,
                    profile.online_time_distribution,
                    profile.financial_literacy,
                    profile.risk_preference,
                    profile.risk_cognition_level,
                    profile.anti_fraud_knowledge,
                    profile.guardian_ids,
                    profile.historical_fraud_victims,
                    profile.created_at,
                    profile.updated_at,
                ),
            )
        self._redis_store.cache_user_profile(user_id, profile.to_dict())
        self._invalidate_cache(self._get_cache_key("SELECT * FROM user_profile WHERE user_id = %s", (user_id,)))
        return profile

    def record_risk_event(self, event: RiskEvent) -> None:
        if not self.is_available:
            self._fallback_events.append(event)
            return

        assert self._conn is not None
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO risk_event (user_id, session_id, risk_stage, scam_type, risk_score, confidence, summary, tags, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,COALESCE(%s, NOW()))
                """,
                (
                    event.user_id,
                    event.session_id,
                    event.risk_stage,
                    event.scam_type,
                    event.risk_score,
                    event.confidence,
                    event.summary,
                    event.tags,
                    event.created_at,
                ),
            )
        self._invalidate_cache(
            self._get_cache_key("SELECT * FROM risk_event WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (event.user_id, 10)),
            self._get_cache_key("SELECT * FROM user_behavior_pattern WHERE user_id = %s", (event.user_id,)),
        )
        self._redis_store.cache_user_behavior_pattern(event.user_id, {})

    def get_recent_risk_events(self, user_id: str, limit: int = 10) -> List[RiskEvent]:
        if not user_id:
            return []
        if not self.is_available:
            filtered = [event for event in self._fallback_events if event.user_id == user_id]
            return filtered[-limit:]

        query = "SELECT * FROM risk_event WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
        params = (user_id, limit)
        cache_key = self._get_cache_key(query, params)
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return [RiskEvent(**row) for row in cached_result]

        assert self._conn is not None
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        payload = [dict(row) for row in rows]
        self._set_cache(cache_key, payload)
        return [RiskEvent(**row) for row in payload]

    def get_behavior_pattern(self, user_id: str) -> Optional[UserBehaviorPattern]:
        if not user_id:
            return None

        cached_pattern = self._redis_store.get_cached_user_behavior_pattern(user_id)
        if cached_pattern:
            return UserBehaviorPattern(**cached_pattern)

        if not self.is_available:
            return self._fallback_patterns.get(user_id, UserBehaviorPattern(user_id=user_id))

        query = "SELECT * FROM user_behavior_pattern WHERE user_id = %s"
        params = (user_id,)
        cache_key = self._get_cache_key(query, params)
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return UserBehaviorPattern(**cached_result)

        assert self._conn is not None
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
        pattern = UserBehaviorPattern(**dict(row)) if row else UserBehaviorPattern(user_id=user_id)
        self._set_cache(cache_key, pattern.to_dict())
        self._redis_store.cache_user_behavior_pattern(user_id, pattern.to_dict())
        return pattern

    def refresh_behavior_pattern(self, user_id: str) -> UserBehaviorPattern:
        events = self.get_recent_risk_events(user_id, limit=200)
        if not events:
            pattern = UserBehaviorPattern(user_id=user_id)
            if not self.is_available:
                self._fallback_patterns[user_id] = pattern
            return pattern

        total_sessions = len({event.session_id for event in events if event.session_id})
        high_risk = [event for event in events if event.risk_stage in {"S3", "S4", "S5", "S6"}]
        most_common = Counter(event.scam_type for event in events if event.scam_type).most_common(1)
        avg_score = sum(event.risk_score for event in events) / len(events)
        risk_trend = self._compute_risk_trend(events)
        last_high_risk_at = max((event.created_at for event in high_risk if event.created_at is not None), default=None)
        pattern = UserBehaviorPattern(
            user_id=user_id,
            total_sessions=total_sessions,
            high_risk_count=len(high_risk),
            most_common_scam_type=most_common[0][0] if most_common else "OTHER_UNKNOWN",
            avg_risk_score=round(avg_score, 4),
            risk_trend=risk_trend,
            last_high_risk_at=last_high_risk_at,
            updated_at=datetime.now(UTC),
        )

        if not self.is_available:
            self._fallback_patterns[user_id] = pattern
            self._redis_store.cache_user_behavior_pattern(user_id, pattern.to_dict())
            return pattern

        assert self._conn is not None
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_behavior_pattern (user_id, total_sessions, high_risk_count, most_common_scam_type,
                    avg_risk_score, risk_trend, last_high_risk_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_sessions = EXCLUDED.total_sessions,
                    high_risk_count = EXCLUDED.high_risk_count,
                    most_common_scam_type = EXCLUDED.most_common_scam_type,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    risk_trend = EXCLUDED.risk_trend,
                    last_high_risk_at = EXCLUDED.last_high_risk_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    pattern.user_id,
                    pattern.total_sessions,
                    pattern.high_risk_count,
                    pattern.most_common_scam_type,
                    pattern.avg_risk_score,
                    pattern.risk_trend,
                    pattern.last_high_risk_at,
                    pattern.updated_at,
                ),
            )
        self._set_cache(self._get_cache_key("SELECT * FROM user_behavior_pattern WHERE user_id = %s", (user_id,)), pattern.to_dict())
        self._redis_store.cache_user_behavior_pattern(user_id, pattern.to_dict())
        return pattern

    def upsert_device_profile(self, profile: UserDeviceProfile) -> None:
        if not self.is_available:
            bucket = self._fallback_device_profiles.setdefault(profile.user_id, [])
            bucket = [item for item in bucket if item.device_id != profile.device_id]
            bucket.append(profile)
            self._fallback_device_profiles[profile.user_id] = bucket
            return

        assert self._conn is not None
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_device_profile (user_id, device_id, device_type, os_version, app_version, last_used_at, security_settings)
                VALUES (%s,%s,%s,%s,%s,COALESCE(%s, NOW()),%s)
                ON CONFLICT (user_id, device_id) DO UPDATE SET
                    device_type = EXCLUDED.device_type,
                    os_version = EXCLUDED.os_version,
                    app_version = EXCLUDED.app_version,
                    last_used_at = EXCLUDED.last_used_at,
                    security_settings = EXCLUDED.security_settings
                """,
                (
                    profile.user_id,
                    profile.device_id,
                    profile.device_type,
                    profile.os_version,
                    profile.app_version,
                    profile.last_used_at,
                    psycopg2.extras.Json(profile.security_settings) if psycopg2 is not None else profile.security_settings,
                ),
            )

    def get_device_profiles(self, user_id: str) -> List[UserDeviceProfile]:
        if not user_id:
            return []
        if not self.is_available:
            return list(self._fallback_device_profiles.get(user_id, []))

        assert self._conn is not None
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM user_device_profile WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
        return [UserDeviceProfile(**dict(row)) for row in rows]

    def record_behavior_event(self, event: UserBehaviorEvent) -> None:
        if not self.is_available:
            self._fallback_behavior_events.append(event)
            return

        assert self._conn is not None
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_behavior_timeline (user_id, event_type, event_data, risk_score, created_at)
                VALUES (%s,%s,%s,%s,COALESCE(%s, NOW()))
                """,
                (
                    event.user_id,
                    event.event_type,
                    psycopg2.extras.Json(event.event_data) if psycopg2 is not None else event.event_data,
                    event.risk_score,
                    event.created_at,
                ),
            )
        self._invalidate_cache(self._get_cache_key("SELECT * FROM user_behavior_timeline WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (event.user_id, 50)))

    def get_behavior_events(self, user_id: str, limit: int = 50) -> List[UserBehaviorEvent]:
        if not user_id:
            return []
        if not self.is_available:
            filtered = [event for event in self._fallback_behavior_events if event.user_id == user_id]
            return filtered[-limit:]

        query = "SELECT * FROM user_behavior_timeline WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
        params = (user_id, limit)
        cache_key = self._get_cache_key(query, params)
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return [UserBehaviorEvent(**row) for row in cached_result]

        assert self._conn is not None
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        payload = [dict(row) for row in rows]
        self._set_cache(cache_key, payload)
        return [UserBehaviorEvent(**row) for row in payload]

    def identify_behavior_patterns(self, user_id: str) -> Dict[str, Any]:
        events = self.get_behavior_events(user_id, limit=100)
        if not events:
            return {"pattern": "unknown", "risk_exposure": "low"}

        event_types = [event.event_type for event in events]
        event_type_counts = Counter(event_types)
        most_common_type = event_type_counts.most_common(1)[0][0] if event_type_counts else "unknown"
        risk_scores = [event.risk_score for event in events]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        high_risk_count = sum(1 for score in risk_scores if score > 0.7)
        if avg_risk_score > 0.6 or high_risk_count > len(events) * 0.3:
            pattern = "high_risk_seeker"
            risk_exposure = "high"
        elif avg_risk_score > 0.3:
            pattern = "moderate_risk"
            risk_exposure = "medium"
        else:
            pattern = "low_risk"
            risk_exposure = "low"
        return {
            "pattern": pattern,
            "risk_exposure": risk_exposure,
            "most_common_event_type": most_common_type,
            "avg_risk_score": round(avg_risk_score, 4),
            "high_risk_count": high_risk_count,
            "total_events": len(events),
        }

    def analyze_user_behavior_timeline(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        events = self.get_behavior_events(user_id, limit=500)
        recent_events = [event for event in events if event.created_at and event.created_at >= cutoff_date]
        if not recent_events:
            return {"timeline_analysis": "no_data", "risk_trend": "stable", "peak_risk_times": []}

        events_by_date: Dict[Any, List[UserBehaviorEvent]] = {}
        for event in recent_events:
            date_key = event.created_at.date() if event.created_at else datetime.now(UTC).date()
            events_by_date.setdefault(date_key, []).append(event)
        daily_risk_scores: Dict[Any, float] = {}
        for date_key, day_events in events_by_date.items():
            scores = [item.risk_score for item in day_events]
            daily_risk_scores[date_key] = sum(scores) / len(scores) if scores else 0.0

        sorted_dates = sorted(daily_risk_scores.keys())
        if len(sorted_dates) < 2:
            risk_trend = "stable"
        else:
            first_half = sorted_dates[: len(sorted_dates) // 2]
            second_half = sorted_dates[len(sorted_dates) // 2 :]
            first_avg = sum(daily_risk_scores[d] for d in first_half) / len(first_half)
            second_avg = sum(daily_risk_scores[d] for d in second_half) / len(second_half)
            if second_avg - first_avg > 0.1:
                risk_trend = "rising"
            elif first_avg - second_avg > 0.1:
                risk_trend = "declining"
            else:
                risk_trend = "stable"

        peak_risk_times = [
            {
                "timestamp": event.created_at.isoformat() if event.created_at else None,
                "risk_score": event.risk_score,
                "event_type": event.event_type,
            }
            for event in recent_events
            if event.risk_score > 0.8
        ]
        return {
            "timeline_analysis": "completed",
            "risk_trend": risk_trend,
            "peak_risk_times": peak_risk_times,
            "daily_risk_scores": {str(date): score for date, score in daily_risk_scores.items()},
            "total_events": len(recent_events),
        }

    def identify_fraud_patterns(self, user_id: str) -> Dict[str, Any]:
        events = self.get_recent_risk_events(user_id, limit=100)
        if not events:
            return {"fraud_patterns": [], "most_common_scam_type": "unknown"}

        scam_types = [event.scam_type for event in events if event.scam_type]
        scam_type_counts = Counter(scam_types)
        most_common_scam = scam_type_counts.most_common(1)[0][0] if scam_type_counts else "unknown"
        risk_stages = [event.risk_stage for event in events if event.risk_stage]
        risk_stage_counts = Counter(risk_stages)
        fraud_patterns: List[Dict[str, Any]] = []
        for scam_type, count in scam_type_counts.items():
            if count >= 3:
                fraud_patterns.append(
                    {
                        "pattern": f"repeated_{scam_type}",
                        "description": f"用户多次遇到{scam_type}类型的诈骗",
                        "count": count,
                        "scam_type": scam_type,
                    }
                )

        sorted_events = sorted(events, key=lambda item: item.created_at or datetime.min)
        if len(sorted_events) >= 3:
            stage_order = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}
            stage_values = [stage_order.get(item.risk_stage, 0) for item in sorted_events]
            for idx in range(len(stage_values) - 2):
                if stage_values[idx] < stage_values[idx + 1] < stage_values[idx + 2]:
                    fraud_patterns.append(
                        {
                            "pattern": "escalating_risk",
                            "description": "用户遇到的风险程度正在升级",
                            "start_stage": sorted_events[idx].risk_stage,
                            "end_stage": sorted_events[idx + 2].risk_stage,
                        }
                    )
                    break

        return {
            "fraud_patterns": fraud_patterns,
            "most_common_scam_type": most_common_scam,
            "scam_type_distribution": dict(scam_type_counts),
            "risk_stage_distribution": dict(risk_stage_counts),
        }

    def segment_users(self, segment_criteria: Dict[str, Any]) -> List[str]:
        if not self.is_available:
            return []

        assert self._conn is not None
        conditions: List[str] = []
        params: List[Any] = []
        for field in [
            "age_group",
            "financial_literacy",
            "risk_preference",
            "risk_cognition_level",
            "anti_fraud_knowledge",
        ]:
            if field in segment_criteria:
                conditions.append(f"{field} = %s")
                params.append(segment_criteria[field])
        query = "SELECT user_id FROM user_profile"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def _compute_risk_trend(events: List[RiskEvent]) -> str:
        dated = [event for event in events if event.created_at is not None]
        if len(dated) < 4:
            return "stable"
        dated.sort(key=lambda item: item.created_at or datetime.min)
        window_size = min(3, max(1, len(dated) // 2))
        moving_averages: List[float] = []
        for idx in range(len(dated) - window_size + 1):
            window = dated[idx : idx + window_size]
            weights = [step + 1 for step in range(window_size)]
            weighted_sum = sum(event.risk_score * weights[pos] for pos, event in enumerate(window))
            moving_averages.append(weighted_sum / sum(weights))
        if len(moving_averages) < 2:
            return "stable"
        first_avg = moving_averages[0]
        last_avg = moving_averages[-1]
        if last_avg - first_avg > 0.1:
            return "rising"
        if first_avg - last_avg > 0.1:
            return "declining"
        return "stable"
