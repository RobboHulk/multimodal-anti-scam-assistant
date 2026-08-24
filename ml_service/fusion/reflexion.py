"""
亮点4 — Reflexion 自我反思与自适应进化
参考 SCoRe (ICLR 2025) 不确定性触发深思机制：
  - 触发条件：confidence < 0.6 或 risk_interval 宽度 > 25 或 consistency_score < 0.5
  - 二次 LLM 调用，输出 ReflectionResult
  - 根据 adjustment 调整 riskScore / chatResponse
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fusion.schemas import MlPredictResult, ReflectionResult
from intent_recognizer import IntentResult
from shared.llm.base import BaseLLM
from shared.llm.factory import create_llm


class FusionReflector:
    """
    SCoRe 不确定性触发深思机制。
    在 FusionLLMCaller.generate() 末尾条件触发。
    """

    # 触发阈值
    CONFIDENCE_THRESHOLD = 0.60
    INTERVAL_WIDTH_THRESHOLD = 25.0
    CONSISTENCY_THRESHOLD = 0.50

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

    # ------------------------------------------------------------------ #
    # 触发判断
    # ------------------------------------------------------------------ #
    def should_reflect(
        self,
        result: MlPredictResult,
        consistency_score: float = 1.0,
    ) -> bool:
        """
        判断是否需要触发自我反思。
        任一条件满足即触发。
        """
        if result.confidence < self.CONFIDENCE_THRESHOLD:
            return True
        interval = result.risk_interval or {}
        if interval.get("width", 0) > self.INTERVAL_WIDTH_THRESHOLD:
            return True
        if consistency_score < self.CONSISTENCY_THRESHOLD:
            return True
        return False

    # ------------------------------------------------------------------ #
    # 自我反思
    # ------------------------------------------------------------------ #
    def reflect(
        self,
        prediction: MlPredictResult,
        intent_result: IntentResult,
        evidence: List[Dict[str, Any]],
        consistency_score: float = 1.0,
    ) -> ReflectionResult:
        """
        二次 LLM 调用，输出 ReflectionResult。
        LLM 不可用时返回 maintain 默认结果。
        """
        if self.llm is None or not self.llm.is_available:
            return self._default_reflection(prediction)

        prompt = self._build_reflection_prompt(
            prediction, intent_result, evidence, consistency_score
        )
        try:
            raw = self.llm.generate(prompt, max_new_tokens=500, temperature=0.1)
            payload = self._extract_json(raw)
            return self._parse_reflection(payload, prediction)
        except Exception:
            return self._default_reflection(prediction)

    # ------------------------------------------------------------------ #
    # 应用反思结果
    # ------------------------------------------------------------------ #
    def apply_adjustment(
        self,
        result: MlPredictResult,
        reflection: ReflectionResult,
    ) -> MlPredictResult:
        """
        根据 ReflectionResult 调整 MlPredictResult。
        """
        result.reflection_note = reflection.reflection_summary

        if reflection.adjustment == "escalate":
            delta = min(reflection.score_delta, 0.15)
            result.risk_score = min(1.0, round(result.risk_score + delta, 4))
            if reflection.reflection_summary:
                result.report = result.report + f"\n\n**反思补充**: {reflection.reflection_summary}"

        elif reflection.adjustment == "deescalate":
            delta = min(reflection.score_delta, 0.10)
            result.risk_score = max(0.0, round(result.risk_score - delta, 4))
            if reflection.reflection_summary:
                result.report = result.report + f"\n\n**反思补充**: {reflection.reflection_summary}"

        elif reflection.adjustment == "clarify":
            if reflection.clarifying_questions:
                questions_text = "\n".join(
                    f"- {q}" for q in reflection.clarifying_questions[:2]
                )
                result.chat_response = (
                    result.chat_response
                    + f"\n\n为了更准确判断，我还需要了解：\n{questions_text}"
                )

        # 高误报/漏报风险时标记
        if reflection.false_positive_risk > 0.6:
            result.metadata["false_positive_risk"] = reflection.false_positive_risk
        if reflection.false_negative_risk > 0.6:
            result.metadata["false_negative_risk"] = reflection.false_negative_risk
            result.metadata["needs_human_review"] = True

        return result

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    def _build_reflection_prompt(
        self,
        prediction: MlPredictResult,
        intent_result: IntentResult,
        evidence: List[Dict[str, Any]],
        consistency_score: float,
    ) -> str:
        evidence_summary = "\n".join(
            f"- {item.get('title', '')}：{str(item.get('snippet', ''))[:80]}"
            for item in evidence[:3]
        )
        interval = prediction.risk_interval or {}
        return f"""你是一个反诈骗判别系统的自我反思模块。请检查以下初步判定结果是否合理。

## 初步判定结果
- riskScore: {prediction.risk_score}
- scamType: {prediction.scam_type}
- confidence: {prediction.confidence}
- riskAction: {prediction.risk_action}
- 置信区间: [{interval.get('lower', '?')}, {interval.get('upper', '?')}]（宽度={interval.get('width', '?')}）
- 跨模态一致性分数: {consistency_score:.2f}

## 意图识别结果
- risk_stage: {intent_result.risk_stage}
- coarse_category: {intent_result.coarse_category}
- primary_signals: {', '.join(intent_result.primary_signals[:5])}
- reasoning: {intent_result.reasoning}

## 检索证据
{evidence_summary or '无检索证据'}

## 反思任务
请检查：
1. 风险分是否合理？是否存在明显的误判（误报/漏报）？
2. 证据是否充分支持当前判定？
3. 是否需要追问用户以获取更多信息？

## 输出要求（严格 JSON）
{{
  "adjustment": "maintain / escalate / deescalate / clarify",
  "score_delta": 0.0-0.15（调整幅度，仅 escalate/deescalate 时有效，与 riskScore 同为 0~1 量纲）,
  "false_positive_risk": 0.0-1.0（误报风险，越高越可能是误报）,
  "false_negative_risk": 0.0-1.0（漏报风险，越高越可能是漏报）,
  "clarifying_questions": ["追问问题1", "追问问题2"],
  "reflection_summary": "反思摘要（50字以内）"
}}

只输出 JSON。"""

    @staticmethod
    def _parse_reflection(
        payload: Dict[str, Any], prediction: MlPredictResult
    ) -> ReflectionResult:
        valid_adjustments = {"maintain", "escalate", "deescalate", "clarify"}
        adjustment = str(payload.get("adjustment", "maintain"))
        if adjustment not in valid_adjustments:
            adjustment = "maintain"
        return ReflectionResult(
            adjustment=adjustment,
            score_delta=float(payload.get("score_delta", 0.0)),
            false_positive_risk=float(payload.get("false_positive_risk", 0.0)),
            false_negative_risk=float(payload.get("false_negative_risk", 0.0)),
            clarifying_questions=[
                str(q) for q in payload.get("clarifying_questions", [])
            ][:3],
            reflection_summary=str(payload.get("reflection_summary", "")).strip(),
        )

    @staticmethod
    def _default_reflection(prediction: MlPredictResult) -> ReflectionResult:
        return ReflectionResult(
            adjustment="maintain",
            score_delta=0.0,
            false_positive_risk=0.0,
            false_negative_risk=0.0,
            clarifying_questions=[],
            reflection_summary="",
        )

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {}
