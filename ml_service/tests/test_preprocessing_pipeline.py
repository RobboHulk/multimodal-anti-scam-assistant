"""多模态预处理模块测试。"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import wave
from unittest.mock import patch

from preprocessing import (
    AudioPreprocessor,
    ImagePreprocessor,
    MultimodalPreprocessingPipeline,
    TextPreprocessor,
    VideoPreprocessor,
)
from preprocessing.asr_client import BaseASRClient, LocalFunASRClient, create_asr_client
from preprocessing.ocr_client import BaseOCRClient, LocalPaddleOCRVLClient, create_ocr_client


class _MockDetailedASR(BaseASRClient):
    def transcribe(self, audio_path: str) -> str:
        return "请立即转账并提供验证码"

    def transcribe_detailed(self, audio_path: str) -> dict:
        return {
            "text": "请立即转账并提供验证码",
            "segments": [
                {"start": 0.0, "end": 1.8, "speaker": "spk_1", "text": "请立即转账"},
                {"start": 1.8, "end": 3.2, "speaker": "spk_2", "text": "并提供验证码"},
            ],
        }


class _MockStructuredOCR(BaseOCRClient):
    def extract(self, image_path: str):
        data = self.extract_structured(image_path)
        return data["ocr_text"], data["ocr_blocks"]

    def extract_structured(self, image_path: str) -> dict:
        return {
            "ocr_text": "立即转账到安全账户，输入验证码",
            "ocr_blocks": [
                {"text": "立即转账", "bbox": [10, 10, 100, 40], "confidence": 0.98},
                {"text": "安全账户", "bbox": [12, 48, 120, 80], "confidence": 0.96},
            ],
            "page_type": "bank_transfer_page",
            "objects": ["转账按钮"],
            "risk_signals": ["转账引导"],
            "layout_summary": "mock_layout",
        }


class PreprocessingPipelineTestCase(unittest.TestCase):
    def test_text_preprocess_normalizes_entities(self) -> None:
        processor = TextPreprocessor()
        result = processor.preprocess("请访问 https://abc.com 并把验证码和1234567890123456银行卡发来")
        self.assertIn("<URL>", result.clean_text)
        self.assertIn("<BANK_CARD>", result.clean_text)
        self.assertTrue(result.global_features.has_verification_code_request)

    def test_pipeline_runs_without_media_files(self) -> None:
        _tmp = tempfile.gettempdir()
        pipeline = MultimodalPreprocessingPipeline()
        output = pipeline.run(
            query="有人让我下载APP并转账",
            image_path=os.path.join(_tmp, "not_exists_image.png"),
            audio_path=os.path.join(_tmp, "not_exists_audio.wav"),
            video_path=os.path.join(_tmp, "not_exists_video.mp4"),
        )
        self.assertTrue(output.text.clean_text)
        self.assertIsNotNone(output.image)
        self.assertIsNotNone(output.audio)
        self.assertIsNotNone(output.video)

    def test_audio_preprocess_prefers_detailed_asr_segments(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "sample.wav"
            with wave.open(str(audio_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * 16000)

            processor = AudioPreprocessor(asr_client=_MockDetailedASR())
            result = processor.preprocess(str(audio_path))
            self.assertEqual(len(result.asr_segments), 2)
            self.assertEqual(result.asr_segments[0].speaker, "spk_1")
            self.assertGreaterEqual(result.audio_features.speaker_count, 2)

    def test_image_preprocess_prefers_structured_ocr(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "sample.jpg"
            image_path.write_bytes(b"\xff\xd8\xff\xd9")
            processor = ImagePreprocessor(ocr_client=_MockStructuredOCR())
            result = processor.preprocess(str(image_path))
            self.assertEqual(result.page_type, "bank_transfer_page")
            self.assertIn("转账按钮", result.objects)
            self.assertTrue(any("转账" in sig for sig in result.risk_signals))

    def test_factory_prefers_local_clients(self) -> None:
        asr_client = create_asr_client()
        ocr_client = create_ocr_client()
        self.assertNotEqual(asr_client.__class__.__name__, "DashScopeASRClient")
        self.assertNotEqual(ocr_client.__class__.__name__, "DashScopeOCRClient")

    def test_local_clients_return_explicit_unavailable_marker(self) -> None:
        _tmp = tempfile.gettempdir()
        missing_asr = LocalFunASRClient(model_path=os.path.join(_tmp, "not_exists_funasr_model"))
        asr_result = missing_asr.transcribe_detailed(os.path.join(_tmp, "anything.wav"))
        self.assertEqual(asr_result.get("text", ""), "")
        self.assertEqual(asr_result.get("status"), "failed")
        self.assertEqual(asr_result.get("error_code"), "LOCAL_MODEL_NOT_AVAILABLE")

        missing_ocr = LocalPaddleOCRVLClient(model_path=os.path.join(_tmp, "not_exists_ocr_model"))
        ocr_result = missing_ocr.extract_structured(os.path.join(_tmp, "anything.png"))
        self.assertEqual(ocr_result.get("ocr_text", ""), "")
        self.assertEqual(ocr_result.get("status"), "failed")
        self.assertEqual(ocr_result.get("error_code"), "LOCAL_MODEL_NOT_AVAILABLE")

    def test_audio_preprocess_reports_deepfake_detector_failure(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "sample.wav"
            with wave.open(str(audio_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * 16000)

            processor = AudioPreprocessor(asr_client=_MockDetailedASR())
            with patch("preprocessing.audio_preprocessor.detect_audio_file", side_effect=RuntimeError("detector missing")):
                result = processor.preprocess(str(audio_path))

            self.assertIn("DEEPFAKE_DETECTOR_NOT_AVAILABLE", result.warnings)
            self.assertFalse(result.audio_features.synthetic_voice_available)

    def test_video_preprocess_file_not_found_has_status(self) -> None:
        processor = VideoPreprocessor()
        result = processor.preprocess(os.path.join(tempfile.gettempdir(), "not_exists_video.mp4"))
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "VIDEO_FILE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()

