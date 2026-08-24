"""主业务 pipeline 与在线接口测试。"""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from knowledge_graph.rag.fraud_rag_pipeline import FraudRAGPipeline
from preprocessing.pipeline import PreprocessOutput
from preprocessing.schema import (
    ASRSegment,
    AudioFeatures,
    AudioPreprocessResult,
    ImagePreprocessResult,
    KeyFrame,
    TextPreprocessResult,
    VideoPreprocessResult,
)


class _MockPreprocessor:
    def run(self, *, query: str, image_path: str = "", audio_path: str = "", video_path: str = "") -> PreprocessOutput:
        return PreprocessOutput(
            text=TextPreprocessResult(clean_text=f"{query}（清洗后）"),
            image=ImagePreprocessResult(
                ocr_text="截图里写着验证码和转账",
                page_type="bank_transfer_page",
                objects=["转账按钮", "验证码输入框"],
                status="ok",
                source_model="mock_ocr",
            ),
            audio=AudioPreprocessResult(
                transcript="请把验证码告诉我",
                asr_segments=[ASRSegment(start=0.0, end=1.0, speaker="unknown", text="请把验证码告诉我")],
                audio_features=AudioFeatures(synthetic_voice_score=0.87, synthetic_voice_available=True),
                status="ok",
                source_model="mock_asr",
            ),
            video=VideoPreprocessResult(
                keyframes=[KeyFrame(time=1.0, page_type="download_page", ocr_text="请下载 app")],
                behavior_sequence=["t=1.0s 页面切换为 download_page"],
                audio_summary=AudioPreprocessResult(
                    transcript="安装这个软件",
                    audio_features=AudioFeatures(synthetic_voice_score=0.91, synthetic_voice_available=True),
                    status="ok",
                    source_model="mock_video_audio",
                ),
                status="ok",
                source_model="mock_video",
            ),
        )


class FraudRAGPipelineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = FraudRAGPipeline(enable_llm=False)

    def test_predict_returns_structured_output(self) -> None:
        result = self.pipeline.predict(
            text="客服说我的订单异常，让我点击链接重新验证并输入验证码",
            session_id="pipeline-1",
        )
        payload = result.to_dict()

        self.assertIn("answer", payload)
        self.assertIn("intent_result", payload)
        self.assertGreater(payload["risk_score"], 0.0)
        self.assertIn(payload["risk_level"], {"low", "medium", "high", "critical"})
        self.assertTrue(payload["intent_result"]["is_fraud_relevant"])

    def test_audio_path_is_connected_into_intent_pipeline(self) -> None:
        _fake_wav = os.path.join(tempfile.gettempdir(), "fake.wav")
        with patch.object(self.pipeline, "preprocessor", _MockPreprocessor()):
            with patch.object(self.pipeline.router, "route", wraps=self.pipeline.router.route) as route_spy:
                result = self.pipeline.predict(
                    text="这段录音像不像骗子冒充客服？",
                    audio_path=_fake_wav,
                    session_id="pipeline-audio",
                )

        kwargs = route_spy.call_args.kwargs
        self.assertEqual(kwargs["image_ocr_text"], "截图里写着验证码和转账")
        self.assertIn("bank_transfer_page", kwargs["image_caption"])
        self.assertEqual(kwargs["audio_text"], "请把验证码告诉我")
        self.assertEqual(kwargs["audio_deepfake_score"], 0.87)
        self.assertIn("preprocessing", kwargs["context"])
        self.assertTrue(result.intent_result.has_audio)
        self.assertEqual(result.multimodal_signals["audio_path"], _fake_wav)
        self.assertGreaterEqual(result.risk_score, 0.0)
        self.assertLessEqual(result.risk_score, 1.0)

    def test_retrieval_hints_include_dual_stream_items(self) -> None:
        result = self.pipeline.predict(
            text="有人让我把验证码发给客服，说要解除账户异常",
            session_id="pipeline-retrieval",
        )
        hints = result.retrieval_hints
        self.assertGreater(len(hints), 0)
        streams = {h.get("stream") for h in hints if "stream" in h}
        self.assertTrue(any(stream in {"q2q", "q2m"} for stream in streams))
        self.assertIsInstance(result.retrieved_evidence, list)
        self.assertIn("retrieval", result.trace)
        self.assertIn("second_hop_hit_count", result.trace["retrieval"])

    def test_answer_consumes_retrieved_evidence(self) -> None:
        result = self.pipeline.predict(
            text="请给我相关法条依据，骗子冒充客服让我转账",
            session_id="pipeline-grounded",
        )
        self.assertIsInstance(result.retrieved_evidence, list)
        self.assertTrue(result.answer.strip())
        if result.retrieved_evidence and not result.intent_result.short_circuit:
            self.assertIn("参考证据", result.answer)

    def test_pipeline_accepts_video_path(self) -> None:
        result = self.pipeline.predict(
            text="对方让我打开视频里的链接下载软件",
            video_path=os.path.join(tempfile.gettempdir(), "not_exists_video.mp4"),
            session_id="pipeline-video",
        )
        self.assertIn(result.risk_level, {"low", "medium", "high", "critical"})

    def test_pipeline_preserves_fusion_risk_score_scale(self) -> None:
        fusion_result = Mock(
            risk_score=0.92,
            report="# 安全监测报告\n\n## 1. 风险结论\n- 风险分数：0.92\n- 诈骗类型：冒充公检法诈骗\n- 处置建议：BLOCK",
            chat_response="这是高危诈骗，请立即停止转账。",
            tags=["安全账户", "冒充公安"],
            scam_type="IMPERSONATE_POLICE_GOV",
            confidence=0.93,
            risk_action="BLOCK",
            risk_interval={"lower": 0.82, "upper": 0.98, "width": 0.16},
            risk_prediction_set=["critical"],
            consistency_score=0.95,
            consistency_report={"consistency_score": 0.95},
            reflection_note="",
            citations=[],
            metadata={"source": "llm_fusion"},
        )
        with patch.object(self.pipeline, "fusion_caller") as fusion_caller:
            fusion_caller.generate.return_value = fusion_result
            result = self.pipeline.predict(
                text="对方冒充公安让我把钱转到安全账户",
                session_id="pipeline-risk-scale",
            )

        self.assertAlmostEqual(result.risk_score, 0.92, places=2)
        self.assertEqual(result.risk_level, "critical")
        self.assertEqual(result.risk_action, "BLOCK")


if __name__ == "__main__":
    unittest.main()

