"""ASR 客户端封装（local_only 本地优先）。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

# 项目根目录（preprocessing/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 与项目仓库同级的 Models 目录（../Models）
_DEFAULT_MODELS_DIR = _PROJECT_ROOT.parent / "Models"

DEFAULT_MODEL_ROOT = os.getenv("LOCAL_MODEL_ROOT", str(_DEFAULT_MODELS_DIR))
DEFAULT_FUNASR_MODEL_PATH = os.getenv(
    "LOCAL_FUNASR_MODEL_PATH", str(Path(DEFAULT_MODEL_ROOT) / "Fun-ASR-Nano-2512")
)


class BaseASRClient:
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

    def transcribe_detailed(self, audio_path: str) -> dict[str, Any]:
        text = self.transcribe(audio_path)
        return {
            "text": text,
            "segments": [],
            "status": "ok",
            "source_model": "unknown",
            "error_code": "",
            "error_message": "",
            "warnings": [],
        }


class DashScopeASRClient(BaseASRClient):
    """
    DashScope ASR 轻封装。

    说明：
    - 由于不同 SDK 版本接口存在差异，这里做温和降级；
    - 若无法调用成功，交由上层 fallback。
    """

    def __init__(self, model: str = "paraformer-realtime-v2", api_key: Optional[str] = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")

    def transcribe(self, audio_path: str) -> str:
        return str(self.transcribe_detailed(audio_path).get("text", "")).strip()

    def transcribe_detailed(self, audio_path: str) -> dict[str, Any]:
        if not self.api_key:
            return self._error_payload("failed", "DASHSCOPE_API_KEY_MISSING", "dashscope key missing")
        try:
            import dashscope
        except ImportError:
            return self._error_payload("failed", "DASHSCOPE_IMPORT_ERROR", "dashscope not installed")

        dashscope.api_key = self.api_key
        # 兼容性调用：无法保证所有环境都支持音频 ASR 类，失败时返回空串。
        try:
            # pylint: disable=import-error
            from dashscope.audio.asr import Recognition  # type: ignore

            response = Recognition.call(
                model=self.model,
                file_urls=[f"file://{Path(audio_path).resolve()}"],
            )
            if getattr(response, "status_code", None) == 200:
                output = getattr(response, "output", {}) or {}
                text = str(output.get("text", "")).strip()
                segments = output.get("sentences", []) or output.get("segments", []) or []
                normalized_segments = []
                for seg in segments:
                    if not isinstance(seg, dict):
                        continue
                    normalized_segments.append(
                        {
                            "start": float(seg.get("begin_time", seg.get("start", 0.0))),
                            "end": float(seg.get("end_time", seg.get("end", 0.0))),
                            "text": str(seg.get("text", "")).strip(),
                            "speaker": str(seg.get("speaker", "other")),
                            "confidence": float(seg.get("confidence", seg.get("prob", 0.0))),
                        }
                    )
                return {
                    "text": text,
                    "segments": normalized_segments,
                    "status": "ok",
                    "source_model": "dashscope_asr",
                    "error_code": "",
                    "error_message": "",
                    "warnings": [],
                }
        except Exception:
            return self._error_payload("failed", "DASHSCOPE_ASR_FAILED", "dashscope asr request failed")
        return self._error_payload("failed", "DASHSCOPE_EMPTY_RESPONSE", "dashscope empty response")

    @staticmethod
    def _error_payload(status: str, error_code: str, error_message: str) -> dict[str, Any]:
        return {
            "text": "",
            "segments": [],
            "status": status,
            "source_model": "dashscope_asr",
            "error_code": error_code,
            "error_message": error_message,
            "warnings": [error_code],
        }


class LocalFunASRClient(BaseASRClient):
    """Fun-ASR 本地模型客户端。"""

    def __init__(self, model_path: str = DEFAULT_FUNASR_MODEL_PATH) -> None:
        self.model_path = str(Path(model_path))
        self._model = None
        self._load_error = ""

    @property
    def is_available(self) -> bool:
        return Path(self.model_path).exists()

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if not self.is_available:
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: {self.model_path}"
            return None
        try:
            from funasr import AutoModel
        except Exception as exc:  # pragma: no cover - 依赖缺失时进入兜底
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: funasr_missing ({exc})"
            return None

        try:
            device = "cuda:0"
            try:
                import torch

                if not torch.cuda.is_available():
                    device = "cpu"
            except Exception:
                device = "cpu"

            remote_code = Path(self.model_path) / "model.py"
            kwargs = {
                "model": self.model_path,
                "trust_remote_code": True,
                "device": device,
            }
            if remote_code.exists():
                kwargs["remote_code"] = str(remote_code)
            self._model = AutoModel(**kwargs)
        except Exception as exc:  # pragma: no cover
            self._load_error = f"LOCAL_MODEL_NOT_AVAILABLE: load_failed ({exc})"
            return None
        return self._model

    def transcribe(self, audio_path: str) -> str:
        return str(self.transcribe_detailed(audio_path).get("text", "")).strip()

    def transcribe_detailed(self, audio_path: str) -> dict[str, Any]:
        model = self._load_model()
        if model is None:
            return self._error_payload(
                "failed",
                "LOCAL_MODEL_NOT_AVAILABLE",
                self._load_error or "local asr model not available",
            )

        wav_path = str(Path(audio_path).resolve())
        try:
            result = model.generate(
                input=[wav_path],
                cache={},
                batch_size_s=300,
                language="中文",
                itn=True,
            )
        except Exception as exc:  # pragma: no cover
            return self._error_payload("failed", "LOCAL_MODEL_INFERENCE_FAILED", str(exc))

        payload = result[0] if isinstance(result, list) and result else {}
        if isinstance(payload, list) and payload:
            payload = payload[0]
        if not isinstance(payload, dict):
            return {
                "text": str(payload),
                "segments": [],
                "status": "degraded",
                "source_model": "funasr_local",
                "error_code": "LOCAL_MODEL_NON_STANDARD_OUTPUT",
                "error_message": "funasr output is not dict",
                "warnings": ["LOCAL_MODEL_NON_STANDARD_OUTPUT"],
            }

        text = str(payload.get("text", "")).strip()
        segments: list[dict[str, Any]] = []
        raw_segments = (
            payload.get("sentences")
            or payload.get("segments")
            or payload.get("sentence_info")
            or payload.get("sentence_timestamp")
            or []
        )
        if isinstance(raw_segments, list):
            for idx, seg in enumerate(raw_segments):
                if not isinstance(seg, dict):
                    continue
                start = float(seg.get("start", seg.get("begin_time", 0.0)))
                end = float(seg.get("end", seg.get("end_time", start)))
                seg_text = str(seg.get("text", "")).strip()
                if not seg_text:
                    continue
                segments.append(
                    {
                        "start": start,
                        "end": max(end, start),
                        "text": seg_text,
                        "speaker": str(seg.get("speaker", f"spk_{(idx % 2) + 1}")),
                        "confidence": float(seg.get("confidence", seg.get("prob", 0.0))),
                    }
                )

        return {
            "text": text,
            "segments": segments,
            "status": "ok",
            "source_model": "funasr_local",
            "error_code": "",
            "error_message": "",
            "warnings": [],
        }

    @staticmethod
    def _error_payload(status: str, error_code: str, error_message: str) -> dict[str, Any]:
        return {
            "text": "",
            "segments": [],
            "status": status,
            "source_model": "funasr_local",
            "error_code": error_code,
            "error_message": error_message,
            "warnings": [error_code],
        }


class FallbackASRClient(BaseASRClient):
    """local_only 模式下模型不可用的兜底实现。"""

    def transcribe(self, audio_path: str) -> str:
        return ""

    def transcribe_detailed(self, audio_path: str) -> dict[str, Any]:
        path_name = Path(audio_path).name
        return {
            "text": "",
            "segments": [],
            "status": "failed",
            "source_model": "fallback_asr",
            "error_code": "LOCAL_MODEL_NOT_AVAILABLE",
            "error_message": f"local asr model unavailable: {path_name}",
            "warnings": ["LOCAL_MODEL_NOT_AVAILABLE"],
        }


def create_asr_client() -> BaseASRClient:
    # local_only: 默认仅走本地 ASR，不自动回退 DashScope
    client = LocalFunASRClient()
    if client.is_available:
        return client
    return FallbackASRClient()

