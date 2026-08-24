"""融合层单次 LLM 调用（含 6 个亮点增强）。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from knowledge_graph.scam_type_taxonomy import PRIMARY_SCAM_TYPES

from fusion.citation_tracker import CitationTracker
from fusion.conformal_predictor import ConformalPredictor
from fusion.cross_modal_verifier import CrossModalVerifier
from fusion.reflexion import FusionReflector
from fusion.schemas import MlPredictResult, RiskEvent, UserBehaviorPattern, UserProfile
from intent_recognizer import IntentResult
from shared.llm.base import BaseLLM
from shared.llm.factory import create_llm


class FusionLLMCaller:
    """
    消费意图识别、RAG 证据、画像与记忆，单次输出面向后端的完整结果。
    串联 6 个亮点增强模块：
      亮点1 ConformalPredictor  — 风险置信区间
      亮点2 CrossModalVerifier  — 跨模态一致性验证
      亮点4 FusionReflector     — 不确定性触发深思
      亮点6 CitationTracker     — 证据引用链
    """

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        llm_provider: str | None = None,
        **llm_kwargs: Any,
    ) -> None:
        self.llm = llm
        if self.llm is None:
            try:
                self.llm = create_llm(llm_provider, **llm_kwargs)
            except Exception:
                self.llm = None

        self._citation_tracker = CitationTracker()
        self._cross_modal_verifier = CrossModalVerifier(llm=self.llm)
        self._conformal_predictor = ConformalPredictor(alpha=0.05)
        self._reflector = FusionReflector(llm=self.llm)

    # ------------------------------------------------------------------ #
    # 主入口
    # ------------------------------------------------------------------ #
    def generate(
        self,
        *,
        query: str,
        intent_result: IntentResult,
        retrieved_evidence: List[Dict[str, Any]],
        user_profile: UserProfile,
        recent_events: List[RiskEvent],
        behavior_pattern: UserBehaviorPattern,
        session_summary: str,
        multimodal_signals: Dict[str, Any],
        user_risk_multiplier: float,
        user_risk_reason: str,
        base_risk_score: float,
        risk_level: str,
    ) -> MlPredictResult:

        # ── 亮点1: 用历史事件校准 Conformal Predictor ──────────────────
        if recent_events:
            self._conformal_predictor.calibrate(recent_events)

        # ── 亮点6 Stage-1: 为证据分配 [REF-N] 标识 ────────────────────
        evidence_with_ids, citation_prompt_block = (
            self._citation_tracker.assign_ids(retrieved_evidence)
        )

        # ── 亮点2: 跨模态一致性验证 ────────────────────────────────────
        ocr_text = multimodal_signals.get("image_ocr_text", "")
        audio_text = multimodal_signals.get("audio_text", "")
        image_caption = multimodal_signals.get("image_caption", "")
        audio_deepfake_score = multimodal_signals.get("audio_deepfake_score")
        video_summary = multimodal_signals.get("video_summary", "")
        consistency_report_dict = self._cross_modal_verifier.verify(
            query,
            ocr_text=ocr_text,
            audio_text=audio_text,
            image_caption=image_caption,
            audio_deepfake_score=audio_deepfake_score,
            video_summary=video_summary,
        )
        consistency_score = float(consistency_report_dict.get("consistency_score", 1.0))
        consistency_prompt = CrossModalVerifier.format_for_prompt(consistency_report_dict)

        # ── 亮点1: 生成置信区间 Prompt 片段 ───────────────────────────
        interval_preview = self._conformal_predictor.predict_interval(base_risk_score)
        interval_prompt = ConformalPredictor.format_for_prompt(interval_preview)

        # ── 核心 LLM 调用 ──────────────────────────────────────────────
        prompt = self._build_prompt(
            query=query,
            intent_result=intent_result,
            evidence_with_ids=evidence_with_ids,
            citation_prompt_block=citation_prompt_block,
            user_profile=user_profile,
            recent_events=recent_events,
            behavior_pattern=behavior_pattern,
            session_summary=session_summary,
            multimodal_signals=multimodal_signals,
            user_risk_multiplier=user_risk_multiplier,
            user_risk_reason=user_risk_reason,
            base_risk_score=base_risk_score,
            risk_level=risk_level,
            consistency_prompt=consistency_prompt,
            interval_prompt=interval_prompt,
        )

        if self.llm is None or not self.llm.is_available:
            result = self._fallback_result(
                query=query,
                intent_result=intent_result,
                retrieved_evidence=retrieved_evidence,
                user_risk_multiplier=user_risk_multiplier,
                user_risk_reason=user_risk_reason,
                base_risk_score=base_risk_score,
            )
        else:
            try:
                raw = self.llm.generate(prompt, max_new_tokens=900, temperature=0.1)
                payload = self._extract_json_dict(raw)
                result = self._payload_to_result(
                    payload,
                    intent_result=intent_result,
                    base_risk_score=base_risk_score,
                    user_risk_multiplier=user_risk_multiplier,
                    user_risk_reason=user_risk_reason,
                )
            except Exception:
                result = self._fallback_result(
                    query=query,
                    intent_result=intent_result,
                    retrieved_evidence=retrieved_evidence,
                    user_risk_multiplier=user_risk_multiplier,
                    user_risk_reason=user_risk_reason,
                    base_risk_score=base_risk_score,
                )

        # ── 亮点6 Stage-2/3: 引用验证 + 构建引用链 ────────────────────
        result.citations = self._citation_tracker.build_citation_chain(
            result.report, evidence_with_ids
        )

        # ── 亮点2: 写入一致性分数 ──────────────────────────────────────
        result.consistency_score = consistency_score
        result.consistency_report = consistency_report_dict

        # ── 亮点1: 写入置信区间 + 结构化预测集 ────────────────────────
        conformal_set = self._conformal_predictor.predict_set(result.risk_score)
        result.risk_interval = conformal_set["interval"]
        result.risk_prediction_set = conformal_set["prediction_set"]
        if conformal_set["interval"].get("needs_human_review"):
            result.metadata["needs_human_review"] = True

        # ── 亮点4: 不确定性触发深思 ────────────────────────────────────
        if self._reflector.should_reflect(result, consistency_score=consistency_score):
            reflection = self._reflector.reflect(
                result, intent_result, retrieved_evidence, consistency_score
            )
            result = self._reflector.apply_adjustment(result, reflection)

        return result

    # ------------------------------------------------------------------ #
    # Prompt 构建
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_prompt(
        *,
        query: str,
        intent_result: IntentResult,
        evidence_with_ids: List[Dict[str, Any]],
        citation_prompt_block: str,
        user_profile: UserProfile,
        recent_events: List[RiskEvent],
        behavior_pattern: UserBehaviorPattern,
        session_summary: str,
        multimodal_signals: Dict[str, Any],
        user_risk_multiplier: float,
        user_risk_reason: str,
        base_risk_score: float,
        risk_level: str,
        consistency_prompt: str,
        interval_prompt: str,
    ) -> str:
        recent_event_items = [
            {
                "risk_stage": e.risk_stage,
                "scam_type": e.scam_type,
                "risk_score": e.risk_score,
                "summary": e.summary,
                "tags": e.tags,
            }
            for e in recent_events[:5]
        ]
        intent_payload = {
            "is_fraud_relevant": intent_result.is_fraud_relevant,
            "coarse_category": intent_result.coarse_category,
            "risk_stage": intent_result.risk_stage,
            "recommended_action": intent_result.recommended_action,
            "confidence": intent_result.confidence,
            "primary_signals": intent_result.primary_signals[:5],
            "clarifying_questions": intent_result.clarifying_questions[:2],
            "reasoning": intent_result.reasoning,
        }
        citation_instruction = CitationTracker.citation_instruction()
        return f"""你是一个多模态反诈融合判别引擎。根据以下信息，输出严格 JSON。

## 输入信号
1. 当前用户输入：{query}
2. 意图识别结果：{json.dumps(intent_payload, ensure_ascii=False, indent=2)}
3. 用户画像：{json.dumps(user_profile.to_dict(), ensure_ascii=False, indent=2)}
4. 历史风险事件：{json.dumps(recent_event_items, ensure_ascii=False, indent=2)}
5. 行为模式：{json.dumps(behavior_pattern.to_dict(), ensure_ascii=False, indent=2)}
6. 短期记忆摘要：{session_summary or '无'}
7. 个性化风险系数：{user_risk_multiplier}，原因：{user_risk_reason}
8. 多模态原始信号：{json.dumps(multimodal_signals, ensure_ascii=False, indent=2)}
9. 当前基础风险分（0-1）：{base_risk_score:.4f}，风险等级：{risk_level}
10. {consistency_prompt}
11. {interval_prompt}

{citation_prompt_block}

## 引用规范
{citation_instruction}

## 输出要求（严格 JSON）
{{
  "riskScore": 0.0-1.0 的小数,
  "scamType": "16 类之一或 OTHER_UNKNOWN",
  "confidence": 0.0-1.0,
  "riskAction": "BLOCK / WARN / EDUCATE / REPORT / VERIFY",
  "tags": ["最多 5 个关键标签"],
  "report": "# 安全监测报告\\n\\n## 1. 风险结论\\n- 风险分数：0.87\\n- 诈骗类型：冒充公检法诈骗\\n- 处置建议：BLOCK\\n\\n## 2. 风险说明\\n用 1 段话概述风险原因，可在句中用 [REF-N] 引用证据。\\n\\n## 3. 关键信号\\n- 信号1：...\\n- 信号2：...\\n- 信号3：...\\n\\n## 4. 防御建议\\n1. ...\\n2. ...\\n3. ...\\n\\n## 5. 补充提示\\n- 若信息不足，提示继续补充截图、录音或聊天上下文。",
  "chatResponse": "面向用户的自然语言短回复，语气温和但明确"
}}

## 报告模板约束
1. report 必须严格使用 5 个一级分节：风险结论 / 风险说明 / 关键信号 / 防御建议 / 补充提示。
2. 风险结论中必须包含“风险分数、诈骗类型、处置建议”3 个条目。
3. 关键信号保留 2~3 条最关键要点，可结合 [REF-N] 引用，但不要原样粘贴 trace、retrievedEvidence、citations JSON。
4. 防御建议固定输出 3 条编号建议，要求可执行。
5. riskScore 对外统一使用 0~1 小数，不要输出 0~100。

## 推理步骤（内部完成，不输出步骤本身）
1. 综合意图识别、检索证据、多模态信号，判断诈骗风险。
2. 结合用户画像、历史事件、行为模式和短期记忆，修正风险分。
3. 参考跨模态一致性分数和置信区间，评估判断可靠性。
4. 让 report 与 chatResponse 保持结论一致。

只输出 JSON，不要输出 Markdown 代码块。"""

    # ------------------------------------------------------------------ #
    # 结果解析
    # ------------------------------------------------------------------ #
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

    @staticmethod
    def _normalize_scam_type(raw: str, fallback: str) -> str:
        """规范化 LLM 输出的 scam_type，防止拼写错误导致无效值。"""
        valid = set(PRIMARY_SCAM_TYPES.keys())
        raw_upper = raw.upper().strip()
        if raw_upper in valid:
            return raw_upper
        # 模糊匹配：找编辑距离最近的合法值
        best, best_score = fallback, 0
        for v in valid:
            # 简单字符重叠比
            common = sum(1 for c in raw_upper if c in v)
            score = common / max(len(raw_upper), len(v), 1)
            if score > best_score:
                best, best_score = v, score
        return best if best_score > 0.6 else fallback

    @staticmethod
    def _display_scam_type(scam_type: str) -> str:
        return str(PRIMARY_SCAM_TYPES.get(scam_type, scam_type))

    @staticmethod
    def _normalize_risk_score(raw_score: Any, fallback: float) -> float:
        try:
            risk_score = float(raw_score)
        except (TypeError, ValueError):
            risk_score = fallback
        if risk_score > 1.0:
            risk_score = risk_score / 100.0
        return max(0.0, min(risk_score, 1.0))

    @staticmethod
    def _clean_line(text: str, fallback: str) -> str:
        cleaned = str(text or "").strip()
        return cleaned or fallback

    @classmethod
    def _build_report(
        cls,
        *,
        risk_score: float,
        scam_type: str,
        risk_action: str,
        summary: str,
        key_signals: List[str],
        defense_advice: List[str],
        note: str,
    ) -> str:
        signal_lines = key_signals[:3] or ["结合当前输入，已检测到可疑风险信号，建议继续补充上下文。"]
        advice_lines = defense_advice[:3] or ["暂停高风险操作，优先通过官方渠道核验。"]
        signals_block = "\n".join(f"- {cls._clean_line(item, '存在可疑风险信号。')}" for item in signal_lines)
        advice_block = "\n".join(
            f"{idx}. {cls._clean_line(item, '暂停高风险操作，优先通过官方渠道核验。')}"
            for idx, item in enumerate(advice_lines, start=1)
        )
        return (
            "# 安全监测报告\n\n"
            "## 1. 风险结论\n"
            f"- 风险分数：{risk_score:.2f}\n"
            f"- 诈骗类型：{cls._display_scam_type(scam_type)}\n"
            f"- 处置建议：{risk_action}\n\n"
            "## 2. 风险说明\n"
            f"{cls._clean_line(summary, '综合多模态输入、检索证据与上下文信息，当前存在较高诈骗风险。')}\n\n"
            "## 3. 关键信号\n"
            f"{signals_block}\n\n"
            "## 4. 防御建议\n"
            f"{advice_block}\n\n"
            "## 5. 补充提示\n"
            f"- {cls._clean_line(note, '若信息仍不完整，建议继续补充截图、录音或聊天上下文，以便进一步核验。')}"
        )

    @staticmethod
    def _payload_to_result(
        payload: Dict[str, Any],
        *,
        intent_result: IntentResult,
        base_risk_score: float,
        user_risk_multiplier: float,
        user_risk_reason: str,
    ) -> MlPredictResult:
        risk_score = FusionLLMCaller._normalize_risk_score(
            payload.get("riskScore"),
            max(0.0, min(base_risk_score * user_risk_multiplier, 1.0)),
        )
        confidence = float(payload.get("confidence", intent_result.confidence))
        raw_scam_type = str(payload.get("scamType", intent_result.coarse_category))
        scam_type = FusionLLMCaller._normalize_scam_type(raw_scam_type, intent_result.coarse_category)
        risk_action = str(payload.get("riskAction", intent_result.recommended_action)).upper()
        tags = [str(t) for t in payload.get("tags", [])][:5]
        report = str(payload.get("report", "")).strip()
        if not report.startswith("# 安全监测报告"):
            report = FusionLLMCaller._build_report(
                risk_score=risk_score,
                scam_type=scam_type,
                risk_action=risk_action,
                summary=str(payload.get("report", "")).strip() or intent_result.reasoning,
                key_signals=tags or intent_result.primary_signals[:3],
                defense_advice=[
                    FusionLLMCaller._fallback_user_advice(risk_action),
                    "通过官方渠道核验对方身份，不要直接相信来电、短信或聊天中的指令。",
                    user_risk_reason or "如已发生转账、泄露验证码或安装可疑软件，请立即联系银行、平台或报警处理。",
                ],
                note="若信息仍不完整，建议继续补充截图、录音或聊天上下文，以便进一步核验。",
            )
        chat_response = str(payload.get("chatResponse", "")).strip()
        if not chat_response:
            chat_response = (
                f'根据当前信息，你的情况疑似涉及“{FusionLLMCaller._display_scam_type(scam_type)}”。'
                f"建议优先执行：{risk_action}。如愿意，可继续补充截图、录音或聊天上下文，我会进一步帮你判断。"
            )
        return MlPredictResult(
            risk_score=risk_score,
            scam_type=scam_type,
            confidence=max(0.0, min(confidence, 1.0)),
            risk_action=risk_action,
            tags=tags,
            report=report,
            chat_response=chat_response,
            user_risk_multiplier=user_risk_multiplier,
            user_risk_reason=user_risk_reason,
            metadata={"source": "llm_fusion"},
        )

    @staticmethod
    def _fallback_result(
        *,
        query: str,
        intent_result: IntentResult,
        retrieved_evidence: List[Dict[str, Any]],
        user_risk_multiplier: float,
        user_risk_reason: str,
        base_risk_score: float,
    ) -> MlPredictResult:
        risk_score = max(0.0, min(round(base_risk_score * user_risk_multiplier, 4), 1.0))
        risk_action = str(intent_result.recommended_action).upper()
        tags = list(dict.fromkeys(
            [*intent_result.primary_signals[:3], *intent_result.cues.tactic_tags[:2]]
        ))[:5]
        key_signals = []
        for i, item in enumerate(retrieved_evidence[:3]):
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            summary = "：".join(part for part in [title, snippet[:80]] if part).strip("：")
            if summary:
                key_signals.append(f"[REF-{i+1}] {summary}")
        if not key_signals:
            key_signals = [*tags[:2], "当前主要依据来自多模态线索抽取与意图识别结果。"]
        report = FusionLLMCaller._build_report(
            risk_score=risk_score,
            scam_type=intent_result.coarse_category,
            risk_action=risk_action,
            summary=intent_result.reasoning or "综合多模态输入、检索证据与个性化画像完成风险分析。",
            key_signals=key_signals,
            defense_advice=[
                FusionLLMCaller._fallback_user_advice(risk_action),
                "通过官方客服电话、银行 APP 或平台站内渠道核验，不要直接回拨陌生号码或点击外部链接。",
                user_risk_reason or "如已转账、泄露验证码或安装可疑软件，请立即联系银行、平台或报警处理。",
            ],
            note="若信息不足，建议继续补充截图、录音或聊天上下文，以便进一步核验。",
        )
        if intent_result.short_circuit and intent_result.short_circuit_response:
            chat_response = intent_result.short_circuit_response
        else:
            chat_response = (
                f'根据当前信息，你的情况更像是“{FusionLLMCaller._display_scam_type(intent_result.coarse_category)}”。'
                f"建议先执行：{intent_result.recommended_action.upper()}。如愿意，可继续补充截图、录音或上下文，我会进一步帮你判断。"
            )
        return MlPredictResult(
            risk_score=risk_score,
            scam_type=intent_result.coarse_category,
            confidence=float(intent_result.confidence),
            risk_action=risk_action,
            tags=tags,
            report=report,
            chat_response=chat_response,
            user_risk_multiplier=user_risk_multiplier,
            user_risk_reason=user_risk_reason,
            metadata={"source": "fallback"},
        )

    @staticmethod
    def _fallback_user_advice(risk_action: str) -> str:
        if risk_action == "BLOCK":
            return "立即中断与对方的交互，不要继续转账、扫码、共享屏幕或安装软件。"
        if risk_action == "REPORT":
            return "尽快保留聊天记录、转账凭证和截图，并联系银行与警方。"
        if risk_action == "WARN":
            return "在核验对方身份前，不要提供验证码、银行卡或个人敏感信息。"
        if risk_action == "VERIFY":
            return "先通过官方渠道核验对方身份与事件真实性，再决定是否继续。"
        return "保持谨慎，避免进一步提供敏感信息或进行资金操作。"
