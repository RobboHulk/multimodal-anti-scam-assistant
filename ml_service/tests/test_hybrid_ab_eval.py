"""三路线 A/B 评测测试。"""

from __future__ import annotations

import unittest

from intent_recognizer.hybrid_ab_eval import HybridABEvaluator, HybridEvalRecord
from knowledge_graph.rag.fraud_rag_pipeline import FraudRAGPipeline


class HybridABEvalTestCase(unittest.TestCase):
    def test_evaluate_three_modes(self) -> None:
        pipeline = FraudRAGPipeline(enable_llm=False)
        evaluator = HybridABEvaluator(pipeline)
        records = [
            HybridEvalRecord(
                query="客服让我点击链接并输入验证码",
                is_fraud_relevant=True,
                coarse_category="PHISHING_LINK_QRCODE",
                risk_stage="S2",
                recommended_action="warn",
            ),
            HybridEvalRecord(
                query="你好，今天怎么样",
                is_fraud_relevant=False,
                coarse_category="OTHER_UNKNOWN",
                risk_stage="S0",
                recommended_action="educate",
            ),
        ]
        report = evaluator.evaluate_modes(records)
        self.assertEqual(report["total"], 2)
        self.assertIn("native_omni", report["modes"])
        self.assertIn("text_fusion", report["modes"])
        self.assertIn("hybrid", report["modes"])
        self.assertIn("avg_latency_ms", report["modes"]["hybrid"])


if __name__ == "__main__":
    unittest.main()

