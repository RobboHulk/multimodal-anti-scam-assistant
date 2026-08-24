"""意图识别模块基础测试。"""

from __future__ import annotations

import os
import tempfile
import unittest

from intent_recognizer import IntentAnalyzer, IntentInput
from knowledge_graph.rag.query_router import IntentQueryRouter
from shared.llm.base import BaseLLM


class _MockLLM(BaseLLM):
    def __init__(self) -> None:
        self.text_calls = 0
        self.multimodal_calls = 0

    @property
    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, *, max_new_tokens: int = 512, temperature: float = 0.1) -> str:
        self.text_calls += 1
        return (
            '{"is_fraud_relevant": true, "coarse_category": "PHISHING_LINK_QRCODE", '
            '"risk_stage": "S2", "recommended_action": "warn", "confidence": 0.71, '
            '"reasoning": "text_route"}'
        )

    def generate_multimodal(self, messages, *, max_new_tokens: int = 512, temperature: float = 0.1) -> str:
        self.multimodal_calls += 1
        return (
            '{"is_fraud_relevant": true, "coarse_category": "PHISHING_LINK_QRCODE", '
            '"risk_stage": "S2", "recommended_action": "warn", "confidence": 0.78, '
            '"reasoning": "multimodal_route"}'
        )


class IntentRecognizerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = IntentAnalyzer(enable_llm=False)

    def test_hard_rule_short_circuit(self) -> None:
        result = self.analyzer.analyze(
            IntentInput(text="对方说我是公安，让我马上把钱转到安全账户配合调查")
        )
        self.assertTrue(result.is_fraud_relevant)
        self.assertTrue(result.short_circuit)
        self.assertEqual(result.recommended_action, "block")
        self.assertEqual(result.safety_rule_triggered, "safe_account_transfer")

    def test_greeting_returns_none_depth(self) -> None:
        result = self.analyzer.analyze(IntentInput(text="你好"))
        self.assertEqual(result.analysis_depth, "NONE")
        self.assertFalse(result.is_fraud_relevant)

    def test_cross_modal_signal_boost(self) -> None:
        result = self.analyzer.analyze(
            IntentInput(
                text="他让我把验证码发给他",
                image_ocr_text="短信验证码 348291，请勿泄露给他人",
            )
        )
        self.assertTrue(result.is_fraud_relevant)
        self.assertIn("验证码", "".join(result.primary_signals) + "".join(result.cues.cross_modal_matches))
        self.assertIn(result.analysis_depth, {"SHALLOW", "DEEP"})

    def test_memory_escalation(self) -> None:
        first = self.analyzer.analyze(
            IntentInput(text="有人让我做兼职刷单", session_id="s1")
        )
        second = self.analyzer.analyze(
            IntentInput(text="现在又让我先转500元保证金", session_id="s1")
        )
        self.assertIn(first.risk_stage, {"S1", "S2", "S3"})
        self.assertIn(second.risk_stage, {"S3", "S4"})
        self.assertGreaterEqual(
            IntentAnalyzer.STAGE_ORDER[second.session_risk_ceiling],
            IntentAnalyzer.STAGE_ORDER[first.session_risk_ceiling],
        )

    def test_query_router_adapter(self) -> None:
        router = IntentQueryRouter(analyzer=self.analyzer)
        result = router.route(text="客服说订单异常让我点击链接处理")
        self.assertTrue(result.is_fraud_relevant)
        self.assertTrue(len(result.target_collections) >= 1)

    def test_video_behavior_is_injected_into_signals(self) -> None:
        result = self.analyzer.analyze(
            IntentInput(
                text="视频里对方让我下载软件并输入验证码",
                video_path=os.path.join(tempfile.gettempdir(), "fake.mp4"),
                context={
                    "preprocessing": {
                        "video": {
                            "behavior_sequence": [
                                "t=1.0s 页面切换为 download_page",
                                "audio:资金或验证码引导",
                            ],
                            "keyframes": [
                                {"time": 1.0, "page_type": "download_page", "ocr_text": "立即下载并安装"},
                            ],
                        }
                    }
                },
            )
        )
        signal_text = " ".join(result.primary_signals)
        self.assertIn("download_page", signal_text)

    def test_llm_mode_native_omni_prefers_multimodal_path(self) -> None:
        mock_llm = _MockLLM()
        analyzer = IntentAnalyzer(enable_llm=True, llm=mock_llm)
        _ = analyzer.analyze(
            IntentInput(
                text="对方让我点击链接并输入验证码处理异常订单",
                image_path=os.path.join(tempfile.gettempdir(), "fake.png"),
                context={"llm_mode": "native_omni"},
            )
        )
        self.assertGreaterEqual(mock_llm.multimodal_calls, 1)

    def test_llm_mode_text_fusion_uses_text_path(self) -> None:
        mock_llm = _MockLLM()
        analyzer = IntentAnalyzer(enable_llm=True, llm=mock_llm)
        _ = analyzer.analyze(
            IntentInput(
                text="对方让我转账并把验证码发给他",
                audio_path=os.path.join(tempfile.gettempdir(), "fake.wav"),
                context={"llm_mode": "text_fusion"},
            )
        )
        self.assertGreaterEqual(mock_llm.text_calls, 1)
        self.assertEqual(mock_llm.multimodal_calls, 0)


if __name__ == "__main__":
    unittest.main()

