"""LLM 抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence


class BaseLLM(ABC):
    """统一的大模型访问接口。"""

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        """文本生成。"""

    def generate_multimodal(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        """多模态生成。默认由子类按需实现。"""
        raise NotImplementedError("当前 LLM 后端暂未实现多模态直接推理接口")

