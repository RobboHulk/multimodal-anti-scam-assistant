"""融合层报告模板与精简返回相关测试。"""

from __future__ import annotations

import unittest

from fusion.fusion_caller import FusionLLMCaller
from fusion.cross_modal_verifier import CrossModalVerifier
from intent_recognizer.schema import CueSet, IntentResult


class FusionReportTemplateTestCase(unittest.TestCase):
    def _intent_result(self) -> IntentResult:
        return IntentResult(
            original_query="对方说我是洗钱嫌疑人，让我转到安全账户",
            cues=CueSet(tactic_tags=["authority_pressure", "verify_code"]),
            analysis_depth="DEEP",
            is_fraud_relevant=True,
            intent="RISK_CHECK",
            coarse_category="IMPERSONATE_POLICE_GOV",
            risk_stage="S4",
            risk_stage_urgency="critical",
            recommended_action="block",
            primary_signals=["转账到安全账户", "冒充公安", "要求提供验证码"],
            missing_evidence=[],
            clarifying_questions=[],
            target_collections=["law_articles", "knowledge_graph"],
            needs_graph_lookup=True,
            needs_second_hop=True,
            short_circuit=False,
            short_circuit_response="",
            confidence=0.93,
            safety_rule_triggered="safe_account_transfer",
            reasoning="对方以公安机关名义要求将资金转入所谓安全账户，并伴随验证码要求，属于典型高危诈骗模式。",
        )

    def test_fallback_report_uses_fixed_template(self) -> None:
        result = FusionLLMCaller(llm=None)._fallback_result(
            query="对方说我是洗钱嫌疑人，让我转到安全账户",
            intent_result=self._intent_result(),
            retrieved_evidence=[
                {
                    "title": "冒充公检法常见话术",
                    "snippet": "骗子常以安全账户、资金清查、涉嫌犯罪等话术要求受害人转账。",
                }
            ],
            user_risk_multiplier=1.0,
            user_risk_reason="已出现高危诈骗信号",
            base_risk_score=0.87,
        )
        self.assertTrue(result.report.startswith("# 安全监测报告"))
        self.assertIn("## 1. 风险结论", result.report)
        self.assertIn("## 2. 风险说明", result.report)
        self.assertIn("## 3. 关键信号", result.report)
        self.assertIn("## 4. 防御建议", result.report)
        self.assertIn("## 5. 补充提示", result.report)
        self.assertLessEqual(result.risk_score, 1.0)

    def test_llm_payload_without_template_is_normalized(self) -> None:
        payload = {
            "riskScore": 87,
            "scamType": "IMPERSONATE_POLICE_GOV",
            "confidence": 0.91,
            "riskAction": "block",
            "tags": ["安全账户", "冒充公安"],
            "report": "对方要求转账到安全账户，并强调案件保密，存在明显诈骗风险。",
            "chatResponse": "",
        }
        result = FusionLLMCaller._payload_to_result(
            payload,
            intent_result=self._intent_result(),
            base_risk_score=0.72,
            user_risk_multiplier=1.0,
            user_risk_reason="",
        )
        self.assertAlmostEqual(result.risk_score, 0.87, places=2)
        self.assertTrue(result.report.startswith("# 安全监测报告"))
        self.assertIn("## 3. 关键信号", result.report)
        self.assertTrue(result.chat_response.strip())


    def test_conformal_interval_uses_zero_to_one_scale(self) -> None:
        caller = FusionLLMCaller(llm=None)
        interval = caller._conformal_predictor.predict_interval(0.92)
        self.assertGreaterEqual(interval["lower"], 0.0)
        self.assertLessEqual(interval["upper"], 1.0)
        self.assertLessEqual(interval["width"], 1.0)

    def test_cross_modal_verifier_flags_high_deepfake_signal(self) -> None:
        report = CrossModalVerifier().verify(
            "对方打电话让我转账",
            audio_text="请立刻把钱转到安全账户",
            audio_deepfake_score=0.91,
            video_summary="page_type=download_page；引导安装软件",
        )
        self.assertIn("deepfake_signal", report["anomaly_flags"])
        self.assertIn("检测到高风险合成语音信号", report["contradictions"])
        self.assertLess(report["consistency_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
