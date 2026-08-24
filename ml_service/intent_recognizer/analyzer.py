"""意图识别主分析器。"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from fusion.memory.postgres_store import PostgresLongTermStore
from intent_recognizer.config import (
    RULE_MODEL_AGREEMENT_BASE,
    RULE_MODEL_AGREEMENT_STAGE_BONUS,
    RULE_MODEL_AGREEMENT_TYPE_BONUS,
    SHALLOW_TO_DEEP_CONFIDENCE_THRESHOLD,
    STAGE_ACTION,
    STAGE_COLLECTIONS,
    STAGE_URGENCY,
)
from intent_recognizer.confidence import ConfidenceCalibrator, ConfidenceSignals
from intent_recognizer.context_analyzer import ContextAnalyzer
from intent_recognizer.cue_extractor import MultiModalCueExtractor
from intent_recognizer.depth_gate import DepthGate
from intent_recognizer.memory import SessionMemoryManager
from intent_recognizer.prompts_v2 import build_deep_intent_prompt, build_shallow_intent_prompt
from intent_recognizer.safety_rules import SafetyRuleEngine, heuristic_risk_stage
from intent_recognizer.schema import AnalysisDepth, IntentInput, IntentResult, IntentType
from knowledge_graph.scam_type_taxonomy import validate_scam_type
from shared.llm.base import BaseLLM
from shared.llm.factory import create_llm

_logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """独立的意图识别分析入口。"""

    STAGE_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5, "S6": 6}

    def __init__(
        self,
        *,
        llm: Optional[BaseLLM] = None,
        llm_provider: str | None = None,
        enable_llm: bool = True,
        cue_extractor: Optional[MultiModalCueExtractor] = None,
        safety_engine: Optional[SafetyRuleEngine] = None,
        depth_gate: Optional[DepthGate] = None,
        memory_manager: Optional[SessionMemoryManager] = None,
        confidence_calibrator: Optional[ConfidenceCalibrator] = None,
        postgres_store: Optional[PostgresLongTermStore] = None,
        context_analyzer: Optional[ContextAnalyzer] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.enable_llm = enable_llm
        self.llm = llm
        if self.llm is None and self.enable_llm:
            try:
                self.llm = create_llm(llm_provider, **(llm_kwargs or {}))
            except Exception:
                self.llm = None
        self.cue_extractor = cue_extractor or MultiModalCueExtractor()
        self.safety_engine = safety_engine or SafetyRuleEngine()
        self.depth_gate = depth_gate or DepthGate()
        self.memory_manager = memory_manager or SessionMemoryManager()
        self.confidence_calibrator = confidence_calibrator or ConfidenceCalibrator()
        self.postgres_store = postgres_store or PostgresLongTermStore()
        self.context_analyzer = context_analyzer or ContextAnalyzer(postgres_store=self.postgres_store)
        self.user_type_strategies = {
            "elderly": {"confidence_weight": 0.8},
            "young": {"confidence_weight": 1.0},
            "tech_savvy": {"confidence_weight": 1.2},
            "financially_literate": {"confidence_weight": 1.1},
            "default": {"confidence_weight": 1.0},
        }

    def analyze(self, intent_input: IntentInput) -> IntentResult:
        session_memory = self.memory_manager.get(intent_input.session_id)
        cues = self.cue_extractor.extract(intent_input)
        safety_decision = self.safety_engine.evaluate(intent_input, cues)
        gate_decision = self.depth_gate.decide(
            intent_input,
            cues,
            safety_decision=safety_decision,
            session_risk_ceiling=session_memory.risk_ceiling,
            session_memory=session_memory,
        )

        if safety_decision is not None:
            result = self._build_safety_result(intent_input, cues, safety_decision, session_memory.risk_ceiling)
            self.memory_manager.update(intent_input.session_id, intent_input, result)
            return result

        if gate_decision.analysis_depth == AnalysisDepth.NONE.value:
            result = self._build_none_result(intent_input, cues, session_memory.risk_ceiling, gate_decision.reasons)
            self.memory_manager.update(intent_input.session_id, intent_input, result)
            return result

        llm_result = None
        if self.llm is not None and self.enable_llm and self.llm.is_available:
            try:
                llm_result = self._analyze_with_llm(intent_input, cues, gate_depth=gate_decision.analysis_depth)
            except Exception:
                llm_result = None

        result = self._build_result_from_signal(
            intent_input=intent_input,
            cues=cues,
            gate_depth=gate_decision.analysis_depth,
            base_result=llm_result,
            session_risk_ceiling=session_memory.risk_ceiling,
            session_memory=session_memory,
        )
        self.memory_manager.update(intent_input.session_id, intent_input, result)
        return result

    def _build_safety_result(self, intent_input: IntentInput, cues, safety_decision, session_risk_ceiling: str) -> IntentResult:
        stage = self._max_stage(safety_decision.risk_stage, session_risk_ceiling)
        category = cues.inferred_scam_type
        return IntentResult(
            original_query=intent_input.text,
            cues=cues,
            analysis_depth=AnalysisDepth.DEEP.value,
            is_fraud_relevant=True,
            intent=self._infer_intent_type(intent_input.text, True),
            coarse_category=validate_scam_type(category),
            risk_stage=stage,
            risk_stage_urgency=STAGE_URGENCY[stage],
            recommended_action=safety_decision.recommended_action,
            primary_signals=[safety_decision.matched_text, *cues.cross_modal_matches[:2]],
            missing_evidence=[],
            clarifying_questions=["是否已经进行了转账、扫码或验证码操作？"],
            target_collections=self._build_target_collections(stage, category),
            needs_graph_lookup=True,
            needs_second_hop=stage in {"S3", "S4", "S5", "S6"},
            short_circuit=True,
            short_circuit_response=safety_decision.response,
            confidence=0.98,
            safety_rule_triggered=safety_decision.rule_name,
            image_path=intent_input.image_path or None,
            audio_path=intent_input.audio_path or None,
            has_image=bool(intent_input.image_ocr_text or intent_input.image_caption),
            has_audio=bool(intent_input.audio_text or intent_input.audio_deepfake_score is not None),
            session_risk_ceiling=stage,
            accumulated_cue_count=cues.total_cue_count(),
            reasoning=f"命中硬规则 {safety_decision.rule_name}，优先执行安全兜底。",
            llm_used=False,
        )

    def _build_none_result(self, intent_input: IntentInput, cues, session_risk_ceiling: str, reasons) -> IntentResult:
        stage = session_risk_ceiling if session_risk_ceiling != "S0" else "S0"
        return IntentResult(
            original_query=intent_input.text,
            cues=cues,
            analysis_depth=AnalysisDepth.NONE.value,
            is_fraud_relevant=False,
            intent=IntentType.GENERAL_CHAT.value,
            coarse_category="OTHER_UNKNOWN",
            risk_stage=stage,
            risk_stage_urgency=STAGE_URGENCY[stage],
            recommended_action="educate",
            primary_signals=[],
            missing_evidence=[],
            clarifying_questions=[],
            target_collections=[],
            needs_graph_lookup=False,
            needs_second_hop=False,
            short_circuit=True,
            short_circuit_response="当前更像是普通对话。如果你怀疑涉及诈骗，可以把对方话术、截图或录音发给我继续判断。",
            confidence=0.85,
            image_path=intent_input.image_path or None,
            audio_path=intent_input.audio_path or None,
            has_image=bool(intent_input.image_ocr_text or intent_input.image_caption),
            has_audio=bool(intent_input.audio_text or intent_input.audio_deepfake_score is not None),
            session_risk_ceiling=session_risk_ceiling,
            accumulated_cue_count=cues.total_cue_count(),
            reasoning="；".join(reasons),
            llm_used=False,
        )

    def _build_result_from_signal(
        self,
        *,
        intent_input: IntentInput,
        cues,
        gate_depth: str,
        base_result: Optional[Dict[str, Any]],
        session_risk_ceiling: str,
        session_memory,
    ) -> IntentResult:
        base_result_dict = base_result or {}
        heuristic_stage = heuristic_risk_stage(intent_input, cues)
        category = validate_scam_type(base_result_dict.get("coarse_category", cues.inferred_scam_type))
        stage = self._max_stage(base_result_dict.get("risk_stage", heuristic_stage), session_risk_ceiling)
        action = base_result_dict.get("recommended_action", STAGE_ACTION[stage])
        is_fraud_relevant = bool(base_result_dict.get("is_fraud_relevant", category != "OTHER_UNKNOWN" or stage != "S0"))
        intent = self._infer_intent_type(intent_input.text, is_fraud_relevant)

        primary_signals = list(base_result_dict.get("primary_signals") or [])
        if not primary_signals:
            primary_signals = [cue.text for cue in cues.all_cues()[:4]]
        video_behaviors = self._extract_video_behaviors(intent_input)
        if video_behaviors:
            primary_signals.extend(video_behaviors[:2])

        missing_evidence = list(base_result_dict.get("missing_evidence") or self._default_missing_evidence(stage))
        clarifying_questions = list(base_result_dict.get("clarifying_questions") or self._default_clarifying_questions(stage))[:2]

        input_user_profile = intent_input.user_profile if isinstance(intent_input.user_profile, dict) else {}
        user_type = self._get_user_type(intent_input.profile_id, input_user_profile)
        user_strategy = self.user_type_strategies.get(user_type, self.user_type_strategies["default"])
        raw_confidence = float(base_result_dict.get("confidence", min(0.55 + cues.cue_density_score * 0.08, 0.93)))
        raw_confidence *= user_strategy["confidence_weight"]

        historical_accuracy = self._get_historical_accuracy(intent_input.profile_id)
        context_consistency = self.context_analyzer.get_context_consistency(intent_input.profile_id, intent_input.text) if intent_input.profile_id else 0.5
        user_profile = self._resolve_user_profile(intent_input.profile_id, input_user_profile)
        user_risk_preference = self._normalize_risk_preference(input_user_profile.get("riskPreference")) if input_user_profile else getattr(user_profile, "risk_preference", "medium") if user_profile else "medium"
        context = {
            "risk_level": "high" if stage in {"S3", "S4", "S5", "S6"} else ("low" if stage == "S0" else "medium"),
            "input_type": "multimodal" if (intent_input.image_path or intent_input.audio_path or intent_input.video_path) else "text_only",
            "user_risk_preference": user_risk_preference,
            "user_type": user_type,
        }
        confidence = self.confidence_calibrator.calibrate(
            ConfidenceSignals(
                model_confidence=raw_confidence,
                self_consistency=base_result_dict.get("_self_consistency", 0.75) if base_result is not None else 0.6,
                rule_model_agreement=self._estimate_rule_model_agreement(
                    category=category,
                    stage=stage,
                    heuristic_stage=heuristic_stage,
                    inferred_type=cues.inferred_scam_type,
                ),
                cue_density_prior=min(cues.cue_density_score / 5.0, 1.0),
                cross_modal_support=1.0 if cues.cross_modal_matches else 0.0,
                historical_accuracy=historical_accuracy,
                context_consistency=context_consistency,
            ),
            context=context,
        )

        reasoning = str(base_result_dict.get("reasoning", "基于规则线索和阶段启发式完成意图分析。"))
        if user_type != "default":
            reasoning += f" [用户类型: {user_type}]"
        target_collections = self._build_target_collections(stage, category)
        needs_graph_lookup = is_fraud_relevant and gate_depth == AnalysisDepth.DEEP.value
        needs_second_hop = stage in {"S3", "S4", "S5", "S6"}
        short_circuit = stage in {"S4", "S5"} or action == "block"

        return IntentResult(
            original_query=intent_input.text,
            cues=cues,
            analysis_depth=gate_depth,
            is_fraud_relevant=is_fraud_relevant,
            intent=intent,
            coarse_category=category,
            risk_stage=stage,
            risk_stage_urgency=STAGE_URGENCY[stage],
            recommended_action=action,
            primary_signals=primary_signals,
            missing_evidence=missing_evidence,
            clarifying_questions=clarifying_questions,
            target_collections=target_collections,
            needs_graph_lookup=needs_graph_lookup,
            needs_second_hop=needs_second_hop,
            short_circuit=short_circuit,
            short_circuit_response=self._build_short_circuit_response(stage, action),
            confidence=round(confidence, 3),
            safety_rule_triggered=None,
            image_path=intent_input.image_path or None,
            audio_path=intent_input.audio_path or None,
            has_image=bool(intent_input.image_ocr_text or intent_input.image_caption),
            has_audio=bool(intent_input.audio_text or intent_input.audio_deepfake_score is not None),
            session_risk_ceiling=stage,
            accumulated_cue_count=cues.total_cue_count(),
            reasoning=reasoning,
            llm_used=base_result is not None,
        )

    def _analyze_with_llm(self, intent_input: IntentInput, cues, *, gate_depth: str) -> Dict[str, Any]:
        if self.llm is None:
            raise RuntimeError("LLM 未初始化")

        memory_summary = self.memory_manager.summarize(intent_input.session_id)
        llm_mode = str(intent_input.context.get("llm_mode", "hybrid")).lower()
        has_native_inputs = bool(intent_input.image_path or intent_input.audio_path or intent_input.video_path)
        use_native_multimodal = llm_mode in {"native_omni", "hybrid"} and has_native_inputs
        stage = heuristic_risk_stage(intent_input, cues)
        task_complexity = self._estimate_task_complexity(intent_input, cues)
        temperature = self._get_dynamic_temperature(stage, task_complexity, gate_depth)

        if gate_depth == AnalysisDepth.DEEP.value:
            prompt = build_deep_intent_prompt(intent_input=intent_input, cues=cues, memory_summary=memory_summary, shallow_result=None)

            def _call_a() -> str:
                return self._call_llm(prompt=prompt, intent_input=intent_input, use_native_multimodal=use_native_multimodal, max_new_tokens=700, temperature=max(0.1, temperature - 0.1))

            def _call_b() -> str:
                return self._call_llm(prompt=prompt, intent_input=intent_input, use_native_multimodal=use_native_multimodal, max_new_tokens=700, temperature=min(0.8, temperature + 0.2))

            with ThreadPoolExecutor(max_workers=2) as pool:
                result_a = self._extract_json_dict(pool.submit(_call_a).result())
                result_b = self._extract_json_dict(pool.submit(_call_b).result())
            result_a["_self_consistency"] = self._compute_self_consistency(result_a, result_b)
            return result_a

        shallow_prompt = build_shallow_intent_prompt(intent_input=intent_input, cues=cues, memory_summary=memory_summary)
        shallow_raw = self._call_llm(
            prompt=shallow_prompt,
            intent_input=intent_input,
            use_native_multimodal=use_native_multimodal,
            max_new_tokens=300,
            temperature=temperature,
        )
        shallow_result = self._extract_json_dict(shallow_raw)
        shallow_confidence = float(shallow_result.get("confidence", 0.5))
        shallow_stage = str(shallow_result.get("risk_stage", stage))
        should_deep = self.depth_gate.should_escalate_to_deep(
            shallow_confidence=shallow_confidence,
            predicted_stage=shallow_stage,
            has_cross_modal=bool(cues.cross_modal_matches),
        )
        if shallow_confidence < SHALLOW_TO_DEEP_CONFIDENCE_THRESHOLD:
            should_deep = True
        if not should_deep:
            return shallow_result

        deep_prompt = build_deep_intent_prompt(
            intent_input=intent_input,
            cues=cues,
            memory_summary=memory_summary,
            shallow_result=shallow_result,
        )
        deep_raw = self._call_llm(
            prompt=deep_prompt,
            intent_input=intent_input,
            use_native_multimodal=use_native_multimodal,
            max_new_tokens=700,
            temperature=temperature,
        )
        deep_result = self._extract_json_dict(deep_raw)
        if "confidence" not in deep_result:
            deep_result["confidence"] = shallow_confidence
        return deep_result

    def _estimate_task_complexity(self, intent_input: IntentInput, cues) -> float:
        complexity = 0.0
        if len(intent_input.text) > 100:
            complexity += 0.5
        elif len(intent_input.text) > 50:
            complexity += 0.3
        if intent_input.image_path or intent_input.audio_path or intent_input.video_path:
            complexity += 0.5
        if cues.total_cue_count() > 5:
            complexity += 0.3
        elif cues.total_cue_count() > 2:
            complexity += 0.1
        if cues.cross_modal_matches:
            complexity += 0.2
        return min(complexity, 1.0)

    def _get_dynamic_temperature(self, stage: str, task_complexity: float, gate_depth: str) -> float:
        base_temp = 0.3
        if stage in {"S3", "S4", "S5", "S6"}:
            base_temp = 0.2
        elif stage in {"S1", "S2"}:
            base_temp = 0.3
        else:
            base_temp = 0.4
        if task_complexity > 0.7:
            base_temp = min(base_temp + 0.2, 0.8)
        elif task_complexity < 0.3:
            base_temp = max(base_temp - 0.1, 0.1)
        if gate_depth != AnalysisDepth.DEEP.value:
            base_temp = min(base_temp + 0.1, 0.8)
        return base_temp

    def _get_user_type(self, user_id: str, input_user_profile: Dict[str, Any] | None = None) -> str:
        user_profile = self._resolve_user_profile(user_id, input_user_profile)
        if not user_profile:
            return "default"
        if getattr(user_profile, "age_group", "") == "elderly":
            return "elderly"
        if getattr(user_profile, "age_group", "") in {"young", "adult"}:
            return "young"
        if getattr(user_profile, "financial_literacy", "") == "high":
            return "financially_literate"
        return "default"

    def _resolve_user_profile(self, user_id: str, input_user_profile: Dict[str, Any] | None = None):
        if input_user_profile:
            return self._profile_from_request(user_id, input_user_profile)
        if not user_id:
            return None
        try:
            return self.postgres_store.get_user_profile(user_id)
        except Exception:
            return None

    def _profile_from_request(self, user_id: str, input_user_profile: Dict[str, Any]):
        from fusion.schemas import UserProfile

        age_group = self._normalize_age_group(input_user_profile.get("ageGroup"))
        gender = self._normalize_gender(input_user_profile.get("gender"))
        occupation = str(input_user_profile.get("occupation") or "")
        risk_preference = self._normalize_risk_preference(input_user_profile.get("riskPreference"))
        return UserProfile(
            user_id=str(input_user_profile.get("id") or user_id or ""),
            age_group=age_group,
            gender=gender,
            occupation=occupation,
            risk_preference=risk_preference,
        )

    @staticmethod
    def _normalize_age_group(value: Any) -> str:
        mapping = {
            0: "unknown",
            1: "young",
            2: "adult",
            3: "elderly",
        }
        try:
            return mapping.get(int(value), "unknown")
        except Exception:
            return "unknown"

    @staticmethod
    def _normalize_gender(value: Any) -> str:
        mapping = {
            0: "unknown",
            1: "male",
            2: "female",
        }
        try:
            return mapping.get(int(value), "unknown")
        except Exception:
            return "unknown"

    @staticmethod
    def _normalize_risk_preference(value: Any) -> str:
        mapping = {
            0: "risk_averse",
            1: "moderate",
            2: "risk_seeking",
        }
        try:
            return mapping.get(int(value), "moderate")
        except Exception:
            return "moderate"

    def _get_historical_accuracy(self, user_id: str) -> float:
        if not user_id:
            return 0.7
        try:
            events = self.postgres_store.get_recent_risk_events(user_id, limit=10)
        except Exception:
            events = []
        if not events:
            return 0.7
        accurate_count = sum(1 for event in events if event.confidence > 0.8)
        return accurate_count / len(events)

    @staticmethod
    def _compute_self_consistency(result_a: Dict[str, Any], result_b: Dict[str, Any]) -> float:
        cat_match = result_a.get("coarse_category") == result_b.get("coarse_category")
        stage_match = result_a.get("risk_stage") == result_b.get("risk_stage")
        return 0.5 + 0.25 * int(cat_match) + 0.25 * int(stage_match)

    def _call_llm(self, *, prompt: str, intent_input: IntentInput, use_native_multimodal: bool, max_new_tokens: int, temperature: float) -> str:
        assert self.llm is not None
        if not use_native_multimodal:
            return self.llm.generate(prompt, max_new_tokens=max_new_tokens, temperature=temperature)
        messages = self._build_multimodal_messages(prompt, intent_input)
        try:
            return self.llm.generate_multimodal(messages, max_new_tokens=max_new_tokens, temperature=temperature)
        except NotImplementedError:
            _logger.warning("多模态 LLM 调用不支持 generate_multimodal，降级到纯文本模式 [mode=%s]", intent_input.context.get("llm_mode", "unknown"))
            return self.llm.generate(prompt, max_new_tokens=max_new_tokens, temperature=temperature)
        except Exception as exc:
            _logger.warning("多模态 LLM 调用失败，降级到纯文本模式 [mode=%s, error=%s]", intent_input.context.get("llm_mode", "unknown"), str(exc)[:120])
            return self.llm.generate(prompt, max_new_tokens=max_new_tokens, temperature=temperature)

    @staticmethod
    def _build_multimodal_messages(prompt: str, intent_input: IntentInput) -> list[dict[str, Any]]:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if intent_input.image_path:
            content.append({"type": "image", "image": intent_input.image_path})
        if intent_input.audio_path:
            content.append({"type": "audio", "audio": intent_input.audio_path})
        if intent_input.video_path:
            content.append({"type": "video", "video": intent_input.video_path})
        return [{"role": "user", "content": content}]

    @staticmethod
    def _extract_json_dict(raw_output: str) -> Dict[str, Any]:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _build_target_collections(self, stage: str, category: str) -> list[str]:
        collections = list(STAGE_COLLECTIONS.get(stage, []))
        if category != "OTHER_UNKNOWN":
            collections.append(f"scam_knowledge::{category.lower()}")
        deduped = []
        seen = set()
        for item in collections:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    @staticmethod
    def _extract_video_behaviors(intent_input: IntentInput) -> list[str]:
        metadata = intent_input.context if isinstance(intent_input.context, dict) else {}
        preprocessing = metadata.get("preprocessing", {}) if isinstance(metadata, dict) else {}
        video = preprocessing.get("video", {}) if isinstance(preprocessing, dict) else {}
        behaviors = video.get("behavior_sequence", []) if isinstance(video, dict) else []
        if not isinstance(behaviors, list):
            return []
        return [str(item).strip() for item in behaviors if str(item).strip()]

    @staticmethod
    def _estimate_rule_model_agreement(*, category: str, stage: str, heuristic_stage: str, inferred_type: str) -> float:
        score = RULE_MODEL_AGREEMENT_BASE
        if category == inferred_type:
            score += RULE_MODEL_AGREEMENT_TYPE_BONUS
        if stage == heuristic_stage:
            score += RULE_MODEL_AGREEMENT_STAGE_BONUS
        return min(score, 1.0)

    def _infer_intent_type(self, query: str, is_fraud_relevant: bool) -> str:
        if not is_fraud_relevant:
            return IntentType.GENERAL_CHAT.value
        if re.search(r"(证据|案例|法律|法规|法条|依据)", query):
            return IntentType.EVIDENCE_LOOKUP.value
        if re.search(r"(怎么防|如何识别|注意什么|怎么判断)", query):
            return IntentType.SAFETY_GUIDANCE.value
        return IntentType.RISK_CHECK.value

    def _max_stage(self, left: str, right: str) -> str:
        normalized_left = left if left in self.STAGE_ORDER else "S0"
        normalized_right = right if right in self.STAGE_ORDER else "S0"
        return normalized_left if self.STAGE_ORDER[normalized_left] >= self.STAGE_ORDER[normalized_right] else normalized_right

    @staticmethod
    def _default_missing_evidence(stage: str) -> list[str]:
        if stage in {"S3", "S4"}:
            return ["对方身份核验信息", "是否已发生转账/下载/共享屏幕操作"]
        if stage == "S5":
            return ["转账记录", "聊天截图", "收款账户信息"]
        return ["对方身份信息", "完整上下文截图"]

    @staticmethod
    def _default_clarifying_questions(stage: str) -> list[str]:
        if stage in {"S3", "S4"}:
            return ["对方是否要求你转账、扫码或共享屏幕？", "是否让你安装陌生 APP 或输入验证码？"]
        if stage == "S5":
            return ["你是否已经转账，金额和时间分别是多少？", "是否保留了聊天记录、支付截图或音频？"]
        return ["对方具体是以什么身份联系你的？", "目前是否索要验证码、个人信息或付款？"]

    @staticmethod
    def _build_short_circuit_response(stage: str, action: str) -> str:
        if stage == "S4":
            return "当前风险极高，请立即停止资金操作，联系银行紧急止付，并同步报警。"
        if stage == "S5":
            return "如果已经发生损失，请立刻保留证据、联系银行和警方，并停止继续转账。"
        if action == "block":
            return "建议立即中断与对方的交互，不要继续提供验证码、转账或安装软件。"
        return ""
