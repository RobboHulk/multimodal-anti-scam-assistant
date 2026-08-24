"""
亮点6 — 证据溯源引用链
参考 VeriCite (arXiv 2025) 三阶段验证：
  Stage-1 NLI：为每条证据分配 [REF-N] 标识，注入 Prompt
  Stage-2 证据选择：后处理验证 LLM 输出的引用是否真实存在（防幻觉）
  Stage-3 答案精炼：构建结构化引用链写入 MlPredictResult.citations
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class Citation:
    ref_id: str          # "[REF-1]"
    source: str          # evidence source label
    title: str
    snippet: str
    score: float
    verified: bool = True   # Stage-2 验证结果


class CitationTracker:
    """VeriCite 三阶段证据引用链追踪器。"""

    # ------------------------------------------------------------------ #
    # Stage-1: 为证据分配 [REF-N] 标识，返回带 ID 的证据列表 + Prompt 片段
    # ------------------------------------------------------------------ #
    def assign_ids(
        self, evidence_list: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        返回 (evidence_with_ids, citation_prompt_block)
        evidence_with_ids: 原始 dict 加上 ref_id 字段
        citation_prompt_block: 注入 Prompt 的证据摘要文本
        """
        tagged: List[Dict[str, Any]] = []
        lines: List[str] = []
        for i, item in enumerate(evidence_list):
            ref_id = f"[REF-{i + 1}]"
            enriched = dict(item)
            enriched["ref_id"] = ref_id
            tagged.append(enriched)
            title = item.get("title", "")
            snippet = str(item.get("snippet", "")).strip()[:120]
            source = item.get("source", "unknown")
            lines.append(f"{ref_id} [{source}] {title}：{snippet}")
        prompt_block = "## 可引用证据\n" + "\n".join(lines) if lines else ""
        return tagged, prompt_block

    # ------------------------------------------------------------------ #
    # Stage-2: 验证 LLM 报告中出现的引用是否真实存在（防幻觉）
    # ------------------------------------------------------------------ #
    def verify_citations(
        self,
        report: str,
        evidence_with_ids: List[Dict[str, Any]],
    ) -> Dict[str, bool]:
        """
        扫描 report 中所有 [REF-N] 标记，检查是否在 evidence_with_ids 中存在。
        返回 {ref_id: is_valid}
        """
        valid_ids = {item["ref_id"] for item in evidence_with_ids if "ref_id" in item}
        found = set(re.findall(r"\[REF-\d+\]", report))
        return {ref: (ref in valid_ids) for ref in found}

    # ------------------------------------------------------------------ #
    # Stage-3: 构建结构化引用链
    # ------------------------------------------------------------------ #
    def build_citation_chain(
        self,
        report: str,
        evidence_with_ids: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        从 report 中提取被引用的证据，构建结构化 Citation 列表。
        只保留 Stage-2 验证通过的引用。
        """
        validity = self.verify_citations(report, evidence_with_ids)
        id_to_item = {
            item["ref_id"]: item
            for item in evidence_with_ids
            if "ref_id" in item
        }
        citations: List[Dict[str, Any]] = []
        for ref_id, is_valid in validity.items():
            item = id_to_item.get(ref_id)
            if item is None:
                continue
            citation = Citation(
                ref_id=ref_id,
                source=str(item.get("source", "unknown")),
                title=str(item.get("title", "")),
                snippet=str(item.get("snippet", "")).strip()[:200],
                score=float(item.get("score", 0.0)),
                verified=is_valid,
            )
            citations.append(
                {
                    "ref_id": citation.ref_id,
                    "source": citation.source,
                    "title": citation.title,
                    "snippet": citation.snippet,
                    "score": citation.score,
                    "verified": citation.verified,
                }
            )
        # 按 ref_id 数字排序
        citations.sort(key=lambda c: int(re.search(r"\d+", c["ref_id"]).group()))
        return citations

    # ------------------------------------------------------------------ #
    # 便捷方法：生成注入 Prompt 的引用指令
    # ------------------------------------------------------------------ #
    @staticmethod
    def citation_instruction() -> str:
        return (
            "在 report 字段中，每当引用上方证据时请使用对应的 [REF-N] 标记，"
            "例如：'根据 [REF-1] 显示，该链接属于已知钓鱼域名。'。"
            "不要捏造不存在的引用编号。"
        )
