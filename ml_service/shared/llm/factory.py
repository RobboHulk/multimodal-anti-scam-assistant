"""LLM 工厂函数。"""

from __future__ import annotations

from typing import Any

from shared.config.llm_config import DEFAULT_LLM_PROVIDER, DEFAULT_LOCAL_MODEL_PATH

from .base import BaseLLM
from .dashscope_llm import DashScopeLLM
from .local_qwen import LocalQwenOmniLLM


def create_llm(provider: str | None = None, **kwargs: Any) -> BaseLLM:
    """根据 provider 创建 LLM 实例。"""
    selected_provider = (provider or DEFAULT_LLM_PROVIDER).lower()
    if selected_provider == "local":
        return LocalQwenOmniLLM(
            model_path=kwargs.pop("model_path", DEFAULT_LOCAL_MODEL_PATH),
            **kwargs,
        )
    if selected_provider == "dashscope":
        return DashScopeLLM(**kwargs)
    raise ValueError(f"不支持的 LLM provider: {selected_provider}")

