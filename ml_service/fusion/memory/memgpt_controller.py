"""
亮点3 — MemGPT 式分层记忆自管理
参考 RMM (ACL 2025) 前瞻+回顾双向反思记忆管理：
  - 前瞻反思 (Prospective)：多粒度动态摘要，提炼关键风险信号
  - 回顾反思 (Retrospective)：基于当前查询检索历史中最相关片段
  - 暴露 memory function tools 供 LLM 自主调用
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from shared.llm.base import BaseLLM
from shared.llm.factory import create_llm


class MemGPTController:
    """
    RMM 前瞻+回顾双向反思记忆控制器。
    在 MemoryWriter.persist() 中调用，替代简单的 _compress_history()。
    """

    # 触发前瞻摘要的历史轮数阈值
    PROSPECTIVE_TRIGGER_TURNS = 8

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
    # 前瞻反思：多粒度动态摘要
    # ------------------------------------------------------------------ #
    def prospective_summary(
        self,
        history: List[str],
        current_risk_stage: str = "S0",
        current_scam_type: str = "OTHER_UNKNOWN",
    ) -> str:
        """
        对当前对话历史做多粒度动态摘要，提炼关键风险信号。
        返回压缩后的摘要字符串，写入 Redis session summary。
        """
        if len(history) < self.PROSPECTIVE_TRIGGER_TURNS:
            return "\n".join(history[-6:])

        if self.llm is None or not self.llm.is_available:
            return self._rule_based_summary(history, current_risk_stage)

        prompt = f"""你是一个反诈骗对话记忆管理器。请对以下对话历史做多粒度摘要。

## 当前风险状态
- 风险阶段: {current_risk_stage}
- 诈骗类型: {current_scam_type}

## 对话历史（最近 {len(history)} 轮）
{chr(10).join(history[-20:])}

## 输出要求（严格 JSON）
{{
  "core_risk_signals": ["关键风险信号1", "关键风险信号2"],
  "user_behavior_clues": ["用户行为线索1"],
  "scam_tactics_observed": ["已观察到的诈骗话术1"],
  "risk_escalation_path": "风险演变路径简述（1句话）",
  "compressed_summary": "120字以内的完整摘要，保留所有风险相关信息"
}}

只输出 JSON，不要输出 Markdown 代码块。"""
        try:
            raw = self.llm.generate(prompt, max_new_tokens=400, temperature=0.1)
            payload = self._extract_json(raw)
            summary_parts = []
            if payload.get("risk_escalation_path"):
                summary_parts.append(f"风险路径: {payload['risk_escalation_path']}")
            if payload.get("core_risk_signals"):
                summary_parts.append("核心信号: " + "、".join(payload["core_risk_signals"][:4]))
            if payload.get("scam_tactics_observed"):
                summary_parts.append("话术: " + "、".join(payload["scam_tactics_observed"][:3]))
            if payload.get("compressed_summary"):
                summary_parts.append(payload["compressed_summary"])
            return "\n".join(summary_parts) if summary_parts else "\n".join(history[-6:])
        except Exception:
            return self._rule_based_summary(history, current_risk_stage)

    # ------------------------------------------------------------------ #
    # 回顾反思：基于当前查询检索历史相关片段
    # ------------------------------------------------------------------ #
    def retrospective_retrieve(
        self,
        query: str,
        history: List[str],
        top_k: int = 4,
    ) -> List[str]:
        """
        从历史中检索与当前查询最相关的片段。
        无 LLM 时回退到关键词匹配。
        """
        if not history:
            return []

        if self.llm is None or not self.llm.is_available:
            return self._keyword_retrieve(query, history, top_k)

        prompt = f"""从以下对话历史中，找出与当前查询最相关的 {top_k} 条记录。

## 当前查询
{query}

## 对话历史
{chr(10).join(f'[{i}] {h}' for i, h in enumerate(history[-20:]))}

## 输出要求（严格 JSON）
{{
  "relevant_indices": [0, 3, 5],
  "relevance_reasons": ["原因1", "原因2", "原因3"]
}}

只输出 JSON。"""
        try:
            raw = self.llm.generate(prompt, max_new_tokens=200, temperature=0.1)
            payload = self._extract_json(raw)
            indices = [int(i) for i in payload.get("relevant_indices", [])]
            recent = history[-20:]
            return [recent[i] for i in indices if 0 <= i < len(recent)]
        except Exception:
            return self._keyword_retrieve(query, history, top_k)

    # ------------------------------------------------------------------ #
    # Memory function tools（供 LLM Prompt 中描述，实际由 MemoryWriter 执行）
    # ------------------------------------------------------------------ #
    @staticmethod
    def memory_tools_description() -> str:
        """返回注入 Prompt 的记忆工具描述。"""
        return """## 记忆管理工具（可在 report 中通过 [MEMORY:action:content] 语法调用）
- [MEMORY:save:关键信息] — 将重要信息存入短期记忆
- [MEMORY:archive:事件摘要] — 将关键风险事件归档到长期记忆
- [MEMORY:compress] — 触发当前短期记忆压缩
示例：[MEMORY:archive:用户已进入资金操作阶段，疑似冒充公安诈骗]"""

    @staticmethod
    def parse_memory_commands(text: str) -> List[Dict[str, str]]:
        """解析 LLM 输出中的 [MEMORY:action:content] 命令。"""
        pattern = r"\[MEMORY:(\w+)(?::([^\]]*))?\]"
        commands = []
        for match in re.finditer(pattern, text):
            action = match.group(1)
            content = match.group(2) or ""
            commands.append({"action": action, "content": content.strip()})
        return commands

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    @staticmethod
    def _rule_based_summary(history: List[str], risk_stage: str) -> str:
        risk_lines = [h for h in history if any(
            kw in h for kw in ["stage=", "风险", "诈骗", "转账", "汇款", "公安", "客服"]
        )]
        recent = history[-6:]
        combined = list(dict.fromkeys(risk_lines[-4:] + recent))
        prefix = f"[风险阶段:{risk_stage}] " if risk_stage != "S0" else ""
        return prefix + "\n".join(combined[:8])

    @staticmethod
    def _keyword_retrieve(query: str, history: List[str], top_k: int) -> List[str]:
        keywords = set(re.findall(r"[\u4e00-\u9fff]{2,}", query))
        scored = []
        for h in history[-20:]:
            score = sum(1 for kw in keywords if kw in h)
            if score > 0:
                scored.append((score, h))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored[:top_k]]

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
