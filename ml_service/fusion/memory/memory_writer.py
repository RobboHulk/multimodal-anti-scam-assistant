"""融合层记忆写入逻辑（含亮点3/5接入）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fusion.memory.memgpt_controller import MemGPTController
from fusion.memory.postgres_store import PostgresLongTermStore
from fusion.memory.redis_store import RedisMemoryStore
from fusion.persona_updater import PersonaUpdater
from fusion.schemas import MlPredictResult, RiskEvent, UserBehaviorEvent
from intent_recognizer import IntentInput, IntentResult
from shared.llm.base import BaseLLM
from shared.llm.factory import create_llm


STAGE_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}


class MemoryWriter:
    def __init__(
        self,
        *,
        redis_store: RedisMemoryStore | None = None,
        postgres_store: PostgresLongTermStore | None = None,
        llm: Optional[BaseLLM] = None,
        llm_provider: str | None = None,
        **llm_kwargs: Any,
    ) -> None:
        self.redis_store = redis_store or RedisMemoryStore()
        self.postgres_store = postgres_store or PostgresLongTermStore(redis_store=self.redis_store)
        self.llm = llm
        if self.llm is None:
            try:
                self.llm = create_llm(llm_provider, **llm_kwargs)
            except Exception:
                self.llm = None
        self._memgpt = MemGPTController(llm=self.llm)
        self._persona_updater = PersonaUpdater(store=self.postgres_store)

    def persist(
        self,
        *,
        session_id: str,
        intent_input: IntentInput,
        intent_result: IntentResult,
        fusion_result: MlPredictResult,
        retrieved_evidence: List[Dict[str, Any]],
        rewritten_query: str = "",
    ) -> None:
        self.redis_store.update_session(session_id, intent_input, intent_result)

        session_memory = self.redis_store.get_session(session_id)
        history = session_memory.history or []
        if len(history) >= MemGPTController.PROSPECTIVE_TRIGGER_TURNS:
            summary = self._memgpt.prospective_summary(
                history,
                current_risk_stage=intent_result.risk_stage,
                current_scam_type=intent_result.coarse_category,
            )
            if summary:
                self.redis_store.get_or_create_summary(session_id, summary=summary)

        memory_commands = MemGPTController.parse_memory_commands(
            fusion_result.report + fusion_result.chat_response
        )
        for cmd in memory_commands:
            if cmd["action"] == "archive" and cmd["content"] and intent_input.profile_id:
                self._handle_archive_command(
                    user_id=intent_input.profile_id,
                    session_id=session_id,
                    content=cmd["content"],
                    intent_result=intent_result,
                    fusion_result=fusion_result,
                )

        stage_value = STAGE_ORDER.get(intent_result.risk_stage, 0)
        if intent_input.profile_id:
            behavior_event = UserBehaviorEvent(
                user_id=intent_input.profile_id,
                event_type="session_end",
                event_data={
                    "session_id": session_id,
                    "text": intent_input.text,
                    "risk_stage": intent_result.risk_stage,
                    "scam_type": fusion_result.scam_type,
                    "risk_score": fusion_result.risk_score,
                    "risk_action": fusion_result.risk_action,
                    "confidence": fusion_result.confidence,
                },
                risk_score=fusion_result.risk_score,
                created_at=datetime.now(UTC),
            )
            self.postgres_store.record_behavior_event(behavior_event)

            if stage_value >= STAGE_ORDER["S2"]:
                tags = list(fusion_result.tags)
                if stage_value >= STAGE_ORDER["S4"] and "guardian_alert" not in tags:
                    tags.append("guardian_alert")
                event_summary = self._build_event_summary(intent_input.text, fusion_result, intent_result)
                if fusion_result.reflection_note:
                    event_summary += f"；反思={fusion_result.reflection_note[:60]}"
                event = RiskEvent(
                    user_id=intent_input.profile_id,
                    session_id=session_id,
                    risk_stage=intent_result.risk_stage,
                    scam_type=fusion_result.scam_type,
                    risk_score=fusion_result.risk_score,
                    confidence=fusion_result.confidence,
                    summary=event_summary,
                    tags=tags,
                    created_at=datetime.now(UTC),
                )
                self.postgres_store.record_risk_event(event)
                self.postgres_store.refresh_behavior_pattern(intent_input.profile_id)

        if intent_input.profile_id and stage_value >= STAGE_ORDER["S2"]:
            self._persona_updater.update_after_session(
                user_id=intent_input.profile_id,
                fusion_result=fusion_result,
                risk_stage=intent_result.risk_stage,
                scam_type=fusion_result.scam_type,
            )

    def _handle_archive_command(
        self,
        *,
        user_id: str,
        session_id: str,
        content: str,
        intent_result: IntentResult,
        fusion_result: MlPredictResult,
    ) -> None:
        event = RiskEvent(
            user_id=user_id,
            session_id=session_id,
            risk_stage=intent_result.risk_stage,
            scam_type=fusion_result.scam_type,
            risk_score=fusion_result.risk_score,
            confidence=fusion_result.confidence,
            summary=f"[LLM归档] {content[:200]}",
            tags=["llm_archived"],
            created_at=datetime.utcnow(),
        )
        self.postgres_store.record_risk_event(event)

    @staticmethod
    def _build_event_summary(
        query: str, fusion_result: MlPredictResult, intent_result: IntentResult
    ) -> str:
        return (
            f"query={query[:80]}；stage={intent_result.risk_stage}；"
            f"type={fusion_result.scam_type}；riskScore={fusion_result.risk_score}；"
            f"action={fusion_result.risk_action}"
        )
