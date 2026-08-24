"""原生 Omni / 文本融合 / 混合路线 A/B 评测。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from knowledge_graph.rag.fraud_rag_pipeline import FraudRAGPipeline


@dataclass
class HybridEvalRecord:
    query: str
    is_fraud_relevant: bool
    coarse_category: str
    risk_stage: str
    recommended_action: str
    image_path: str = ""
    audio_path: str = ""
    video_path: str = ""
    image_ocr_text: str = ""
    image_caption: str = ""
    audio_text: str = ""
    audio_deepfake_score: float | None = None


class HybridABEvaluator:
    """对三条路线做统一指标对比。"""

    def __init__(self, pipeline: FraudRAGPipeline) -> None:
        self.pipeline = pipeline

    def evaluate_modes(
        self,
        records: Iterable[HybridEvalRecord],
        *,
        llm_modes: Sequence[str] = ("native_omni", "text_fusion", "hybrid"),
    ) -> Dict[str, Any]:
        rows = list(records)
        results: Dict[str, Any] = {"total": len(rows), "modes": {}}
        for mode in llm_modes:
            results["modes"][mode] = self._evaluate_single_mode(rows, mode)
        return results

    def _evaluate_single_mode(self, rows: List[HybridEvalRecord], llm_mode: str) -> Dict[str, Any]:
        if not rows:
            return {"total": 0}

        fraud_correct = 0
        stage_correct = 0
        category_correct = 0
        action_correct = 0
        latency_ms_total = 0.0
        samples: List[Dict[str, Any]] = []

        import time

        for idx, row in enumerate(rows):
            start = time.perf_counter()
            pred = self.pipeline.predict(
                text=row.query,
                session_id=f"ab-{llm_mode}-{idx}",
                image_path=row.image_path,
                audio_path=row.audio_path,
                video_path=row.video_path,
                user_profile={},
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latency_ms_total += elapsed_ms

            intent = pred.intent_result
            fraud_correct += int(intent.is_fraud_relevant == row.is_fraud_relevant)
            stage_correct += int(intent.risk_stage == row.risk_stage)
            category_correct += int(intent.coarse_category == row.coarse_category)
            action_correct += int(intent.recommended_action == row.recommended_action)
            samples.append(
                {
                    "query": row.query,
                    "expected_stage": row.risk_stage,
                    "pred_stage": intent.risk_stage,
                    "pred_category": intent.coarse_category,
                    "pred_action": intent.recommended_action,
                    "latency_ms": round(elapsed_ms, 3),
                }
            )

        total = len(rows)
        return {
            "total": total,
            "fraud_relevance_accuracy": round(fraud_correct / total, 4),
            "risk_stage_accuracy": round(stage_correct / total, 4),
            "category_accuracy": round(category_correct / total, 4),
            "action_accuracy": round(action_correct / total, 4),
            "avg_latency_ms": round(latency_ms_total / total, 3),
            "samples": samples,
        }

    @staticmethod
    def load_jsonl(path: str) -> List[HybridEvalRecord]:
        records: List[HybridEvalRecord] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(HybridEvalRecord(**payload))
        return records

