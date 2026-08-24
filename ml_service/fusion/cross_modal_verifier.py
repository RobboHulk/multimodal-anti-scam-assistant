"""
亮点2 — 跨模态一致性验证
参考 OmniHallu (ICLR 2025) 多 agent claim 分解验证：
  - 将多模态输入分解为可验证的 claim
  - 跨模态交叉检验，检测语义矛盾与异常不一致
  - 输出 ConsistencyReport，注入 FusionLLMCaller Prompt
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from shared.llm.base import BaseLLM


class CrossModalVerifier:
    """OmniHallu 式跨模态一致性验证器。"""

    # 关键词级快速矛盾检测规则（无需 LLM）
    _CONTRADICTION_PAIRS: List[tuple[str, str]] = [
        ("转账", "不需要转账"),
        ("汇款", "不需要汇款"),
        ("安全", "危险"),
        ("官方", "非官方"),
        ("免费", "收费"),
        ("中奖", "未中奖"),
        ("公安", "骗子"),
        ("客服", "诈骗"),
    ]

    def __init__(self, llm: Optional[BaseLLM] = None) -> None:
        self.llm = llm

    def verify(
        self,
        text: str,
        ocr_text: str = "",
        audio_text: str = "",
        image_caption: str = "",
        audio_deepfake_score: float | None = None,
        video_summary: str = "",
    ) -> Dict[str, Any]:
        """
        返回 ConsistencyReport dict，包含：
          consistency_score: float [0,1]，越低越不一致
          contradictions: List[str]
          anomaly_flags: List[str]
          modality_scores: Dict[str, float]
          needs_clarification: bool
        """
        active_modalities = {
            "text": text.strip(),
            "ocr": ocr_text.strip(),
            "audio": audio_text.strip(),
            "image_caption": image_caption.strip(),
            "video_summary": video_summary.strip(),
        }
        active_modalities = {k: v for k, v in active_modalities.items() if v}

        if len(active_modalities) <= 1 and audio_deepfake_score is None:
            return self._single_modality_report(active_modalities)

        # Stage-1: 关键词级快速矛盾检测
        keyword_contradictions = self._keyword_contradiction_check(active_modalities)

        # Stage-2: LLM claim 分解验证（有 LLM 时启用）
        llm_report: Dict[str, Any] = {}
        if self.llm is not None and self.llm.is_available:
            llm_report = self._llm_claim_verification(active_modalities)

        # Stage-3: 综合评分
        return self._aggregate_report(
            active_modalities, keyword_contradictions, llm_report, audio_deepfake_score
        )

    # ------------------------------------------------------------------ #
    # Stage-1: 关键词级矛盾检测
    # ------------------------------------------------------------------ #
    def _keyword_contradiction_check(
        self, modalities: Dict[str, str]
    ) -> List[str]:
        contradictions: List[str] = []
        combined = " ".join(modalities.values())
        for pos, neg in self._CONTRADICTION_PAIRS:
            if pos in combined and neg in combined:
                contradictions.append(f"检测到矛盾信号：'{pos}' vs '{neg}'")
        return contradictions

    # ------------------------------------------------------------------ #
    # Stage-2: LLM claim 分解验证
    # ------------------------------------------------------------------ #
    def _llm_claim_verification(
        self, modalities: Dict[str, str]
    ) -> Dict[str, Any]:
        modal_desc = "\n".join(
            f"- [{k}]: {v[:200]}" for k, v in modalities.items()
        )
        prompt = f"""你是一个多模态内容一致性验证器。请分析以下来自不同模态的内容，检测是否存在语义矛盾或异常不一致。

## 各模态内容
{modal_desc}

## 输出要求（严格 JSON）
{{
  "consistency_score": 0.0-1.0（1.0=完全一致，0.0=严重矛盾）,
  "contradictions": ["矛盾描述1", "矛盾描述2"],
  "anomaly_flags": ["异常标记1"],
  "modality_scores": {{"text_ocr": 0.9, "text_audio": 0.8, "ocr_audio": 0.85}},
  "analysis": "简短分析"
}}

只输出 JSON，不要输出 Markdown 代码块。"""
        try:
            raw = self.llm.generate(prompt, max_new_tokens=400, temperature=0.1)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
                cleaned = re.sub(r"```$", "", cleaned).strip()
            return json.loads(cleaned)
        except Exception:
            return {}

    # ------------------------------------------------------------------ #
    # Stage-3: 综合评分
    # ------------------------------------------------------------------ #
    def _aggregate_report(
        self,
        modalities: Dict[str, str],
        keyword_contradictions: List[str],
        llm_report: Dict[str, Any],
        audio_deepfake_score: float | None = None,
    ) -> Dict[str, Any]:
        contradictions = list(keyword_contradictions)
        anomaly_flags: List[str] = []

        if llm_report:
            contradictions.extend(llm_report.get("contradictions", []))
            anomaly_flags.extend(llm_report.get("anomaly_flags", []))
            llm_score = float(llm_report.get("consistency_score", 1.0))
        else:
            llm_score = 1.0

        # 关键词矛盾每条扣 0.15
        keyword_penalty = min(len(keyword_contradictions) * 0.15, 0.45)
        consistency_score = round(max(0.0, min(llm_score - keyword_penalty, 1.0)), 3)

        if audio_deepfake_score is not None:
            score = max(0.0, min(float(audio_deepfake_score), 1.0))
            if score >= 0.8:
                anomaly_flags.append("deepfake_signal")
                contradictions.append("检测到高风险合成语音信号")
                consistency_score = round(max(0.0, consistency_score - 0.2), 3)
            elif score >= 0.5:
                anomaly_flags.append("possible_deepfake_signal")
                consistency_score = round(max(0.0, consistency_score - 0.08), 3)

        # 异常标记
        if consistency_score < 0.4:
            anomaly_flags.append("high_inconsistency")
        if "deepfake" in " ".join(modalities.values()).lower():
            anomaly_flags.append("deepfake_signal")

        modality_scores = llm_report.get("modality_scores", {})
        needs_clarification = consistency_score < 0.5 or len(contradictions) > 0

        return {
            "consistency_score": consistency_score,
            "contradictions": list(dict.fromkeys(contradictions)),  # 去重
            "anomaly_flags": list(dict.fromkeys(anomaly_flags)),
            "modality_scores": modality_scores,
            "needs_clarification": needs_clarification,
            "active_modalities": list(modalities.keys()),
        }

    @staticmethod
    def _single_modality_report(modalities: Dict[str, str]) -> Dict[str, Any]:
        return {
            "consistency_score": 1.0,
            "contradictions": [],
            "anomaly_flags": [],
            "modality_scores": {},
            "needs_clarification": False,
            "active_modalities": list(modalities.keys()),
        }

    @staticmethod
    def format_for_prompt(report: Dict[str, Any]) -> str:
        """将 ConsistencyReport 格式化为 Prompt 注入文本。"""
        score = report.get("consistency_score", 1.0)
        contradictions = report.get("contradictions", [])
        flags = report.get("anomaly_flags", [])
        lines = [f"跨模态一致性分数: {score:.2f}"]
        if contradictions:
            lines.append("检测到矛盾: " + "；".join(contradictions[:3]))
        if flags:
            lines.append("异常标记: " + "、".join(flags))
        if report.get("needs_clarification"):
            lines.append("建议: 多模态信号存在不一致，需结合更多上下文判断")
        return "\n".join(lines)
