"""Phase 1-3 新增能力测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from intent_recognizer.confidence import ConfidenceCalibrator, ConfidenceSignals
from intent_recognizer.depth_gate import DepthGate
from intent_recognizer.dspy_optimizer import IntentDSPyOptimizer
from intent_recognizer.evaluator import IntentEvaluator
from intent_recognizer.schema import CueSet, IntentInput

# 项目根目录（tests/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_EVAL_DATASET = str(_PROJECT_ROOT / "intent_recognizer" / "data" / "eval_dataset.jsonl")


class IntentPhase123TestCase(unittest.TestCase):
    def test_confidence_calibrator_output_range(self) -> None:
        calibrator = ConfidenceCalibrator(temperature=1.2)
        score = calibrator.calibrate(
            ConfidenceSignals(
                model_confidence=0.82,
                self_consistency=0.75,
                rule_model_agreement=0.7,
                cue_density_prior=0.6,
                cross_modal_support=1.0,
                historical_accuracy=0.9,
                context_consistency=0.8,
            ),
            context={"risk_level": "high", "input_type": "multimodal", "user_risk_preference": "risk_averse"},
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_depth_gate_escalation(self) -> None:
        self.assertTrue(
            DepthGate.should_escalate_to_deep(
                shallow_confidence=0.62,
                predicted_stage="S2",
                has_cross_modal=False,
            )
        )
        self.assertTrue(
            DepthGate.should_escalate_to_deep(
                shallow_confidence=0.85,
                predicted_stage="S4",
                has_cross_modal=False,
            )
        )
        self.assertFalse(
            DepthGate.should_escalate_to_deep(
                shallow_confidence=0.86,
                predicted_stage="S1",
                has_cross_modal=False,
            )
        )

    def test_depth_gate_predict_thresholds_is_callable(self) -> None:
        gate = DepthGate()
        none_threshold, deep_threshold = gate.predict_thresholds(
            IntentInput(text="客服让我点击链接输入验证码"),
            CueSet(cue_density_score=1.2, inferred_scam_type="PHISHING_LINK_QRCODE"),
        )
        self.assertGreaterEqual(none_threshold, 0.0)
        self.assertGreater(deep_threshold, none_threshold)

    def test_eval_dataset_can_be_loaded(self) -> None:
        records = IntentEvaluator.load_jsonl(_EVAL_DATASET)
        self.assertGreater(len(records), 0)

    def test_dspy_optimizer_fallback_runs(self) -> None:
        optimizer = IntentDSPyOptimizer(max_bootstrapped_demos=2)
        records = IntentEvaluator.load_jsonl(_EVAL_DATASET)
        with TemporaryDirectory() as tmp_dir:
            result = optimizer.optimize(
                train_records=records[:4],
                val_records=records[4:6],
                output_path=f"{tmp_dir}/few_shot_demos.test.json",
            )
        self.assertIn(result["status"], {"ok", "fallback_no_dspy"})


if __name__ == "__main__":
    unittest.main()

