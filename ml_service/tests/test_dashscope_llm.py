"""DashScope LLM 路径转换相关测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.llm.dashscope_llm import DashScopeLLM


class DashScopeLLMTestCase(unittest.TestCase):
    def test_windows_local_path_is_resolved(self) -> None:
        path = DashScopeLLM._resolve_local_path(
            r"D:\Desktop\multimodal_antifraud_agent\evaluation\test_image_generated.png"
        )
        self.assertIsNotNone(path)
        self.assertEqual(
            str(path),
            r"D:\Desktop\multimodal_antifraud_agent\evaluation\test_image_generated.png",
        )

    def test_already_prefixed_file_uri_is_resolved_to_local_path(self) -> None:
        path = DashScopeLLM._resolve_local_path("file:///D:/data/sample.png")
        self.assertIsNotNone(path)
        self.assertEqual(str(path), r"D:\data\sample.png")

    def test_http_url_is_preserved(self) -> None:
        llm = DashScopeLLM(api_key="test-key")
        uri = llm._to_accessible_url("https://example.com/demo.png")
        self.assertEqual(uri, "https://example.com/demo.png")

    def test_local_file_prefers_uploaded_url(self) -> None:
        llm = DashScopeLLM(api_key="test-key")
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "sample.png"
            image_path.write_bytes(b"png")
            with patch.object(llm, "_upload_local_file", return_value="https://oss.example.com/sample.png") as mocked:
                uri = llm._to_accessible_url(str(image_path))
        self.assertEqual(uri, "https://oss.example.com/sample.png")
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
