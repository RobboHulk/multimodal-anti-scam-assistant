"""OCR 客户端封装（local_only 本地优先）。"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, List, Tuple

# 项目根目录（preprocessing/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 与项目仓库同级的 Models 目录（../Models）
_DEFAULT_MODELS_DIR = _PROJECT_ROOT.parent / "Models"

DEFAULT_MODEL_ROOT = os.getenv("LOCAL_MODEL_ROOT", str(_DEFAULT_MODELS_DIR))
DEFAULT_PADDLEOCR_VL_MODEL_PATH = os.getenv(
    "LOCAL_PADDLEOCR_VL_MODEL_PATH", str(Path(DEFAULT_MODEL_ROOT) / "PaddleOCR-VL-1.5")
)


class BaseOCRClient:
    def extract(self, image_path: str) -> Tuple[str, List[dict]]:
        raise NotImplementedError

    def extract_structured(self, image_path: str) -> dict[str, Any]:
        text, blocks = self.extract(image_path)
        return {
            "ocr_text": text,
            "ocr_blocks": blocks,
            "page_type": "unknown_page",
            "objects": [],
            "risk_signals": [],
            "layout_summary": "",
            "status": "ok",
            "source_model": "unknown",
            "error_code": "",
            "error_message": "",
            "warnings": [],
        }


class DashScopeOCRClient(BaseOCRClient):
    def __init__(self, model: str = "qwen-vl-plus", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")

    def extract(self, image_path: str) -> Tuple[str, List[dict]]:
        structured = self.extract_structured(image_path)
        return str(structured.get("ocr_text", "")), list(structured.get("ocr_blocks", []))

    def extract_structured(self, image_path: str) -> dict[str, Any]:
        if not self.api_key:
            return self._error_payload("failed", "DASHSCOPE_API_KEY_MISSING", "dashscope key missing")
        try:
            import dashscope
            from dashscope import MultiModalConversation
        except ImportError:
            return self._error_payload("failed", "DASHSCOPE_IMPORT_ERROR", "dashscope not installed")

        dashscope.api_key = self.api_key
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"file://{Path(image_path).resolve()}"},
                        {
                            "text": (
                                "请提取截图中的文字与结构化信息，仅输出 JSON，字段包含："
                                "ocr_text(string), ocr_blocks(list[{text,bbox,confidence}]), "
                                "page_type(string), objects(list), risk_signals(list), layout_summary(string)。"
                            )
                        },
                    ],
                }
            ]
            response = MultiModalConversation.call(model=self.model, messages=messages)
            if getattr(response, "status_code", None) != 200:
                return self._error_payload("failed", "DASHSCOPE_OCR_FAILED", "dashscope ocr request failed")
            content = response.output.choices[0].message.content[0].get("text", "")
            payload = self._parse_json(str(content))
            if not isinstance(payload, dict):
                return {
                    "ocr_text": "",
                    "ocr_blocks": [],
                    "page_type": "unknown_page",
                    "objects": [],
                    "risk_signals": [],
                    "layout_summary": "",
                    "status": "degraded",
                    "source_model": "dashscope_ocr",
                    "error_code": "DASHSCOPE_NON_JSON_OUTPUT",
                    "error_message": str(content)[:300],
                    "warnings": ["DASHSCOPE_NON_JSON_OUTPUT"],
                }
            return {
                "ocr_text": str(payload.get("ocr_text", "")).strip(),
                "ocr_blocks": list(payload.get("ocr_blocks", [])),
                "page_type": str(payload.get("page_type", "unknown_page")),
                "objects": list(payload.get("objects", [])),
                "risk_signals": list(payload.get("risk_signals", [])),
                "layout_summary": str(payload.get("layout_summary", "")),
                "status": "ok",
                "source_model": "dashscope_ocr",
                "error_code": "",
                "error_message": "",
                "warnings": [],
            }
        except Exception:
            return self._error_payload("failed", "DASHSCOPE_OCR_EXCEPTION", "dashscope ocr exception")

    @staticmethod
    def _error_payload(status: str, error_code: str, error_message: str) -> dict[str, Any]:
        return {
            "ocr_text": "",
            "ocr_blocks": [],
            "page_type": "unknown_page",
            "objects": [],
            "risk_signals": [],
            "layout_summary": "",
            "status": status,
            "source_model": "dashscope_ocr",
            "error_code": error_code,
            "error_message": error_message,
            "warnings": [error_code],
        }

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any] | None:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else None
        except Exception:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
            except Exception:
                return None
            return data if isinstance(data, dict) else None


class LocalPaddleOCRVLClient(BaseOCRClient):
    """PaddleOCR-VL 本地模型客户端。"""

    def __init__(self, model_path: str = DEFAULT_PADDLEOCR_VL_MODEL_PATH) -> None:
        self.model_path = str(Path(model_path))
        self._pipeline = None
        self._load_error = ""

    @property
    def is_available(self) -> bool:
        return Path(self.model_path).exists()

    def _load_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline
        if not self.is_available:
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: {self.model_path}"
            return None
        try:
            from paddleocr import PaddleOCRVL
        except Exception as exc:  # pragma: no cover
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: paddleocr_missing ({exc})"
            return None
        try:
            self._pipeline = PaddleOCRVL(model_name=self.model_path)
        except TypeError:
            try:
                self._pipeline = PaddleOCRVL(model_dir=self.model_path)
            except Exception as exc:  # pragma: no cover
                self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: load_failed ({exc})"
                return None
        except Exception as exc:  # pragma: no cover
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: load_failed ({exc})"
            return None
        return self._pipeline

    def extract(self, image_path: str) -> Tuple[str, List[dict]]:
        structured = self.extract_structured(image_path)
        return str(structured.get("ocr_text", "")), list(structured.get("ocr_blocks", []))

    def extract_structured(self, image_path: str) -> dict[str, Any]:
        pipeline = self._load_pipeline()
        if pipeline is None:
            return {
                "ocr_text": "",
                "ocr_blocks": [],
                "page_type": "unknown_page",
                "objects": [],
                "risk_signals": [],
                "layout_summary": "local_model_unavailable",
                "status": "failed",
                "source_model": "paddleocr_vl_local",
                "error_code": "LOCAL_MODEL_NOT_AVAILABLE",
                "error_message": self._load_error or "local ocr model not available",
                "warnings": ["LOCAL_MODEL_NOT_AVAILABLE"],
            }
        try:
            output = pipeline.predict(str(Path(image_path).resolve()))
            if isinstance(output, list) and output:
                output = output[0]
            if hasattr(output, "to_dict"):
                output = output.to_dict()
            if not isinstance(output, dict):
                return {
                    "ocr_text": "",
                    "ocr_blocks": [],
                    "page_type": "unknown_page",
                    "objects": [],
                    "risk_signals": [],
                    "layout_summary": "local_raw_text_only",
                    "status": "degraded",
                    "source_model": "paddleocr_vl_local",
                    "error_code": "LOCAL_MODEL_NON_STANDARD_OUTPUT",
                    "error_message": str(output)[:300],
                    "warnings": ["LOCAL_MODEL_NON_STANDARD_OUTPUT"],
                }
            return self._normalize_output(output)
        except Exception as exc:  # pragma: no cover
            return {
                "ocr_text": "",
                "ocr_blocks": [],
                "page_type": "unknown_page",
                "objects": [],
                "risk_signals": [],
                "layout_summary": "local_inference_failed",
                "status": "failed",
                "source_model": "paddleocr_vl_local",
                "error_code": "LOCAL_MODEL_INFERENCE_FAILED",
                "error_message": str(exc),
                "warnings": ["LOCAL_MODEL_INFERENCE_FAILED"],
            }

    @staticmethod
    def _normalize_output(output: dict[str, Any]) -> dict[str, Any]:
        # 尽量兼容 PaddleOCR-VL 不同版本返回格式
        ocr_text = ""
        blocks: list[dict[str, Any]] = []
        objects: list[str] = []
        risk_signals: list[str] = []
        page_type = "unknown_page"
        layout_summary = ""

        if "ocr_text" in output:
            ocr_text = str(output.get("ocr_text", "")).strip()
        else:
            texts = []
            for key in ("texts", "rec_texts", "text_lines"):
                value = output.get(key, [])
                if isinstance(value, list):
                    texts.extend(str(item) for item in value if str(item).strip())
            ocr_text = "\n".join(texts).strip()

        raw_blocks = output.get("ocr_blocks") or output.get("blocks") or output.get("text_blocks") or []
        if isinstance(raw_blocks, list):
            for blk in raw_blocks:
                if isinstance(blk, dict):
                    blocks.append(
                        {
                            "text": str(blk.get("text", "")),
                            "bbox": list(blk.get("bbox", blk.get("box", [])) or []),
                            "confidence": float(blk.get("confidence", blk.get("score", 0.0)) or 0.0),
                        }
                    )

        page_type = str(output.get("page_type", "unknown_page"))
        layout_summary = str(output.get("layout_summary", output.get("layout", "")))

        if isinstance(output.get("objects"), list):
            objects = [str(item) for item in output["objects"] if str(item).strip()]
        if isinstance(output.get("risk_signals"), list):
            risk_signals = [str(item) for item in output["risk_signals"] if str(item).strip()]

        if not ocr_text and blocks:
            ocr_text = "\n".join(str(blk.get("text", "")).strip() for blk in blocks if blk.get("text")).strip()

        return {
            "ocr_text": ocr_text,
            "ocr_blocks": blocks,
            "page_type": page_type,
            "objects": objects,
            "risk_signals": risk_signals,
            "layout_summary": layout_summary,
            "status": "ok",
            "source_model": "paddleocr_vl_local",
            "error_code": "",
            "error_message": "",
            "warnings": [],
        }


class FallbackOCRClient(BaseOCRClient):
    def extract(self, image_path: str) -> Tuple[str, List[dict]]:
        structured = self.extract_structured(image_path)
        return str(structured.get("ocr_text", "")), list(structured.get("ocr_blocks", []))

    def extract_structured(self, image_path: str) -> dict[str, Any]:
        path_name = Path(image_path).name
        return {
            "ocr_text": "",
            "ocr_blocks": [],
            "page_type": "unknown_page",
            "objects": [],
            "risk_signals": [],
            "layout_summary": "local_model_unavailable",
            "status": "failed",
            "source_model": "fallback_ocr",
            "error_code": "LOCAL_MODEL_NOT_AVAILABLE",
            "error_message": f"local ocr model unavailable: {path_name}",
            "warnings": ["LOCAL_MODEL_NOT_AVAILABLE"],
        }


def create_ocr_client() -> BaseOCRClient:
    # local_only: 默认仅走本地 OCR，不自动回退 DashScope
    client = LocalPaddleOCRVLClient()
    if client.is_available:
        return client
    return FallbackOCRClient()

