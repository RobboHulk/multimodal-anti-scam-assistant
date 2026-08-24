"""DashScope LLM 封装 — 统一使用 qwen-omni-turbo 全模态模型。

qwen-omni-turbo 支持：文本 / 图片 / 音频 / 视频，与本地 Qwen2.5-Omni-7B 同系列。
- 文本推理：generate()
- 多模态推理：generate_multimodal()，消息 content 可包含 image_url / audio / video
"""

from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List, Mapping, Optional, Sequence

from shared.config.llm_config import (
    DEFAULT_DASHSCOPE_MODEL,
    DEFAULT_DASHSCOPE_MULTIMODAL_MODEL,
)

from .base import BaseLLM

try:
    import dashscope
    from dashscope import Files, MultiModalConversation

    DASHSCOPE_AVAILABLE = True
except ImportError:
    Files = None
    DASHSCOPE_AVAILABLE = False


class DashScopeLLM(BaseLLM):
    """
    基于 DashScope qwen-omni-turbo 的统一封装。

    文本调用和多模态调用都走 MultiModalConversation，
    因为 qwen-omni-turbo 原生支持纯文本输入，无需区分接口。
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        text_model: str = DEFAULT_DASHSCOPE_MODEL,
        multimodal_model: str = DEFAULT_DASHSCOPE_MULTIMODAL_MODEL,
    ) -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        # 两者默认都是 qwen-omni-turbo，保留参数以便未来切换
        self.text_model = text_model
        self.multimodal_model = multimodal_model
        self._uploaded_file_cache: Dict[str, str] = {}
        if DASHSCOPE_AVAILABLE and self.api_key:
            dashscope.api_key = self.api_key

    @property
    def is_available(self) -> bool:
        return bool(DASHSCOPE_AVAILABLE and self.api_key)

    def _ensure_available(self) -> None:
        if not DASHSCOPE_AVAILABLE:
            raise RuntimeError("当前环境未安装 dashscope，请执行: pip install dashscope")
        if not self.api_key:
            raise RuntimeError(
                "未设置 DASHSCOPE_API_KEY，请在终端执行: "
                "$env:DASHSCOPE_API_KEY='sk-xxx'"
            )

    @staticmethod
    def _extract_content(response: Any) -> str:
        """从 DashScope 响应中提取文本内容。"""
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope 调用失败 [{response.status_code}]: "
                f"{getattr(response, 'message', response)}"
            )
        content = response.output.choices[0].message.content
        if isinstance(content, list):
            fragments = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    fragments.append(item["text"])
                else:
                    fragments.append(str(item))
            return "\n".join(fragments).strip()
        return str(content).strip()

    # ------------------------------------------------------------------ #
    # 文本生成（纯文本 prompt → qwen-omni-turbo）
    # ------------------------------------------------------------------ #
    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 900,
        temperature: float = 0.1,
    ) -> str:
        self._ensure_available()
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        response = MultiModalConversation.call(
            model=self.text_model,
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        return self._extract_content(response)

    # ------------------------------------------------------------------ #
    # 多模态生成（图片 / 音频 / 视频 + 文本 → qwen-omni-turbo）
    # ------------------------------------------------------------------ #
    def generate_multimodal(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_new_tokens: int = 900,
        temperature: float = 0.1,
    ) -> str:
        """
        多模态推理入口。

        messages 格式（OpenAI 兼容）：
        [
          {
            "role": "user",
            "content": [
              {"type": "text",      "text": "..."},
              {"type": "image_url", "image_url": {"url": "https://... 或 file:///..."}},
              {"type": "audio",     "audio": {"url": "file:///path/to/audio.wav"}},
              {"type": "video",     "video": {"url": "file:///path/to/video.mp4"}},
            ]
          }
        ]

        本方法会自动将 file:// 路径转换为 DashScope 期望的格式。
        """
        self._ensure_available()
        normalized = self._normalize_messages(list(messages))
        response = MultiModalConversation.call(
            model=self.multimodal_model,
            messages=normalized,
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        return self._extract_content(response)

    # ------------------------------------------------------------------ #
    # 辅助：消息格式标准化
    # ------------------------------------------------------------------ #
    def _normalize_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        将内部消息格式统一为 DashScope MultiModalConversation 期望的格式。

        DashScope qwen-omni-turbo content item 格式：
          - 文本:  {"text": "..."}
          - 图片:  {"image": "url_or_base64"}
          - 音频:  {"audio": "url_or_base64"}
          - 视频:  {"video": "url_or_base64"}

        对本地多媒体文件，优先自动上传为 DashScope 可访问 URL，
        避免 Windows file URI 在服务端解析失败。
        """
        normalized = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, str):
                normalized.append({"role": role, "content": [{"text": content}]})
                continue

            if not isinstance(content, list):
                normalized.append({"role": role, "content": [{"text": str(content)}]})
                continue

            items: List[Dict[str, Any]] = []
            for item in content:
                if not isinstance(item, dict):
                    items.append({"text": str(item)})
                    continue

                item_type = item.get("type", "")

                if item_type == "text" or "text" in item:
                    items.append({"text": item.get("text", item.get("text", ""))})

                elif item_type == "image_url":
                    url = (item.get("image_url") or {}).get("url", "")
                    items.append({"image": self._to_accessible_url(url)})

                elif item_type == "image":
                    url = item.get("image", "")
                    items.append({"image": self._to_accessible_url(url)})

                elif item_type == "audio":
                    audio_payload = item.get("audio", "")
                    url = audio_payload if isinstance(audio_payload, str) else (audio_payload or {}).get("url", "")
                    items.append({"audio": self._to_accessible_url(url)})

                elif item_type == "video":
                    video_payload = item.get("video", "")
                    url = video_payload if isinstance(video_payload, str) else (video_payload or {}).get("url", "")
                    items.append({"video": self._to_accessible_url(url)})

                else:
                    items.append(item)

            normalized.append({"role": role, "content": items})
        return normalized

    def _to_accessible_url(self, url: str) -> str:
        """
        将多模态资源路径转换为 DashScope 可访问 URL。
        - http/https/data URL 直接返回
        - 本地文件优先上传为 DashScope 临时 OSS URL
        - 上传失败时退回 file URI，便于保留兼容性
        """
        if not url:
            return url

        normalized = str(url).strip().strip('"').strip("'")
        if not normalized:
            return normalized
        if normalized.startswith(("http://", "https://", "data:")):
            return normalized

        local_path = self._resolve_local_path(normalized)
        if local_path and local_path.exists() and local_path.is_file():
            uploaded_url = self._upload_local_file(local_path)
            if uploaded_url:
                return uploaded_url
            return local_path.resolve().as_uri()

        if normalized.startswith("file://"):
            return normalized
        return normalized

    @staticmethod
    def _resolve_local_path(url: str) -> Path | None:
        if not url:
            return None
        normalized = str(url).strip().strip('"').strip("'")
        if not normalized:
            return None
        if normalized.startswith(("http://", "https://", "data:")):
            return None
        if normalized.startswith("file://"):
            candidate = normalized[7:]
            if candidate.startswith("/") and len(candidate) >= 3 and candidate[2] == ":":
                candidate = candidate[1:]
            candidate = candidate.replace("/", "\\") if os.name == "nt" else candidate
            return Path(candidate)

        windows_like = (
            len(normalized) >= 3
            and normalized[1] == ":"
            and normalized[0].isalpha()
            and normalized[2] in {"\\", "/"}
        )
        if windows_like:
            return Path(str(PureWindowsPath(normalized)))
        return Path(normalized)

    def _upload_local_file(self, path: Path) -> str:
        cache_key = str(path.resolve())
        cached = self._uploaded_file_cache.get(cache_key)
        if cached:
            return cached
        if not DASHSCOPE_AVAILABLE or Files is None:
            return ""

        response = Files.upload(
            file_path=str(path),
            purpose="inference",
            api_key=self.api_key,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope 文件上传失败 [{response.status_code}]: {getattr(response, 'message', response)}"
            )

        uploaded_files = (response.output or {}).get("uploaded_files") or []
        if not uploaded_files:
            raise RuntimeError("DashScope 文件上传成功但未返回 uploaded_files")
        file_id = uploaded_files[0].get("file_id", "")
        if not file_id:
            raise RuntimeError("DashScope 文件上传成功但未返回 file_id")

        detail = Files.get(file_id, api_key=self.api_key)
        if detail.status_code != 200:
            raise RuntimeError(
                f"DashScope 文件详情查询失败 [{detail.status_code}]: {getattr(detail, 'message', detail)}"
            )
        uploaded_url = (detail.output or {}).get("url", "")
        if not uploaded_url:
            raise RuntimeError("DashScope 文件详情未返回可访问 url")
        self._uploaded_file_cache[cache_key] = uploaded_url
        return uploaded_url
