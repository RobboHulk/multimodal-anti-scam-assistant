"""DSPy 自动化 Prompt 优化入口。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from intent_recognizer.evaluator import IntentEvalRecord

try:
    import dspy
except ImportError:  # pragma: no cover
    dspy = None


@dataclass
class OptimizedPromptArtifact:
    optimizer: str
    metric_name: str
    score: float
    instructions: Dict[str, Any]
    demos: List[Dict[str, Any]]


def fraud_metric(expected: Dict[str, Any], predicted: Dict[str, Any]) -> float:
    """综合指标：相关性 > 风险阶段 > 主类 > 动作。"""
    score = 0.0
    if expected.get("is_fraud_relevant") == predicted.get("is_fraud_relevant"):
        score += 0.4
    if expected.get("risk_stage") == predicted.get("risk_stage"):
        score += 0.25
    if expected.get("coarse_category") == predicted.get("coarse_category"):
        score += 0.2
    if expected.get("recommended_action") == predicted.get("recommended_action"):
        score += 0.15
    return round(score, 4)


class IntentDSPyOptimizer:
    """对意图识别 Prompt 做自动优化（MIPROv2 优先）。"""

    def __init__(self, *, model_name: str = "qwen-plus", max_bootstrapped_demos: int = 4) -> None:
        self.model_name = model_name
        self.max_bootstrapped_demos = max_bootstrapped_demos

    @staticmethod
    def load_eval_records(path: str) -> List[IntentEvalRecord]:
        records: List[IntentEvalRecord] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            records.append(IntentEvalRecord(**json.loads(line)))
        return records

    def optimize(
        self,
        *,
        train_records: Iterable[IntentEvalRecord],
        val_records: Optional[Iterable[IntentEvalRecord]] = None,
        output_path: str = "intent_recognizer/data/few_shot_demos.json",
    ) -> Dict[str, Any]:
        train_records = list(train_records)
        val_records = list(val_records or [])
        if not train_records:
            raise ValueError("train_records 不能为空")

        if dspy is None:
            artifact = OptimizedPromptArtifact(
                optimizer="fallback",
                metric_name="fraud_metric",
                score=0.0,
                instructions={"note": "未安装 dspy，已导出基线样例。"},
                demos=[self._record_to_demo(r) for r in train_records[: self.max_bootstrapped_demos]],
            )
            self._write_artifact(output_path, artifact)
            return {"status": "fallback_no_dspy", "output_path": output_path, "artifact": artifact.__dict__}

        import os
        from dspy.teleprompt import MIPROv2

        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            artifact = OptimizedPromptArtifact(
                optimizer="fallback_no_api_key",
                metric_name="fraud_metric",
                score=0.0,
                instructions={"note": "未设置 DASHSCOPE_API_KEY，已导出基线样例。"},
                demos=[self._record_to_demo(r) for r in train_records[: self.max_bootstrapped_demos]],
            )
            self._write_artifact(output_path, artifact)
            return {"status": "fallback_no_api_key", "output_path": output_path, "artifact": artifact.__dict__}
        lm = dspy.LM(
            model=f"openai/{self.model_name}",
            api_key=api_key,
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        dspy.configure(lm=lm)

        trainset = [
            dspy.Example(
                query=r.query,
                image_ocr_text=r.image_ocr_text or "",
                image_caption=r.image_caption or "",
                audio_text=r.audio_text or "",
                audio_deepfake_score=r.audio_deepfake_score,
                is_fraud_relevant=r.is_fraud_relevant,
                coarse_category=r.coarse_category,
                risk_stage=r.risk_stage,
                recommended_action=r.recommended_action,
            ).with_inputs("query", "image_ocr_text", "image_caption", "audio_text", "audio_deepfake_score")
            for r in train_records
        ]

        class FraudIntentSignature(dspy.Signature):
            """反诈意图分析：判断是否诈骗相关，给出类别、风险阶段和推荐动作。"""
            query: str = dspy.InputField(desc="用户输入文本")
            image_ocr_text: str = dspy.InputField(desc="图片 OCR 文本")
            image_caption: str = dspy.InputField(desc="图片描述")
            audio_text: str = dspy.InputField(desc="音频 ASR 文本")
            audio_deepfake_score: float = dspy.InputField(desc="音频 deepfake 分数")
            is_fraud_relevant: bool = dspy.OutputField(desc="是否诈骗相关")
            coarse_category: str = dspy.OutputField(desc="诈骗主类")
            risk_stage: str = dspy.OutputField(desc="风险阶段 S0-S6")
            recommended_action: str = dspy.OutputField(desc="推荐动作")

        program = dspy.Predict(FraudIntentSignature)

        def _dspy_metric(example, pred, trace=None):
            return fraud_metric(
                {
                    "is_fraud_relevant": example.is_fraud_relevant,
                    "coarse_category": example.coarse_category,
                    "risk_stage": example.risk_stage,
                    "recommended_action": example.recommended_action,
                },
                {
                    "is_fraud_relevant": getattr(pred, "is_fraud_relevant", None),
                    "coarse_category": getattr(pred, "coarse_category", None),
                    "risk_stage": getattr(pred, "risk_stage", None),
                    "recommended_action": getattr(pred, "recommended_action", None),
                },
            )

        teleprompter = MIPROv2(
            metric=_dspy_metric,
            num_candidates=10,
            init_temperature=1.0,
            verbose=True,
        )
        optimized = teleprompter.compile(
            program,
            trainset=trainset,
            num_trials=20,
            minibatch_size=min(25, len(trainset)),
        )

        # 提取优化后的 instructions 和 demos
        optimized_instructions = {}
        optimized_demos = []
        for pred_name, predictor in optimized.named_predictors():
            if hasattr(predictor, "extended_signature"):
                optimized_instructions[pred_name] = predictor.extended_signature.instructions
            if hasattr(predictor, "demos"):
                for demo in predictor.demos:
                    optimized_demos.append(demo.toDict() if hasattr(demo, "toDict") else dict(demo))

        # 在 val_records 上评估最终分数
        final_score = 0.0
        if val_records:
            scores = []
            for r in val_records:
                pred = optimized(
                    query=r.query,
                    image_ocr_text=r.image_ocr_text or "",
                    image_caption=r.image_caption or "",
                    audio_text=r.audio_text or "",
                    audio_deepfake_score=r.audio_deepfake_score,
                )
                scores.append(fraud_metric(
                    {"is_fraud_relevant": r.is_fraud_relevant, "coarse_category": r.coarse_category,
                     "risk_stage": r.risk_stage, "recommended_action": r.recommended_action},
                    {"is_fraud_relevant": getattr(pred, "is_fraud_relevant", None),
                     "coarse_category": getattr(pred, "coarse_category", None),
                     "risk_stage": getattr(pred, "risk_stage", None),
                     "recommended_action": getattr(pred, "recommended_action", None)},
                ))
            final_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        artifact = OptimizedPromptArtifact(
            optimizer="MIPROv2",
            metric_name="fraud_metric",
            score=final_score,
            instructions=optimized_instructions,
            demos=optimized_demos,
        )
        self._write_artifact(output_path, artifact)
        return {"status": "ok", "output_path": output_path, "artifact": artifact.__dict__}

    @staticmethod
    def _record_to_demo(record: IntentEvalRecord) -> Dict[str, Any]:
        return {
            "input": {
                "query": record.query,
                "image_ocr_text": record.image_ocr_text,
                "image_caption": record.image_caption,
                "audio_text": record.audio_text,
                "audio_deepfake_score": record.audio_deepfake_score,
            },
            "output": {
                "is_fraud_relevant": record.is_fraud_relevant,
                "coarse_category": record.coarse_category,
                "risk_stage": record.risk_stage,
                "recommended_action": record.recommended_action,
            },
        }

    @staticmethod
    def _estimate_stub_score(records: Iterable[IntentEvalRecord]) -> float:
        # 保留兼容接口，真实评分已在 optimize() 中实现
        return 0.0

    @staticmethod
    def _write_artifact(output_path: str, artifact: OptimizedPromptArtifact) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(artifact.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

