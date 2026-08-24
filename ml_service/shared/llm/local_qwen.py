"""本地 Qwen 模型封装。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .base import BaseLLM


class LocalQwenOmniLLM(BaseLLM):
    """懒加载的本地 Qwen2.5-Omni 封装。"""

    def __init__(
        self,
        model_path: str,
        *,
        device_map: str = "auto",
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
        load_on_init: bool = False,
    ) -> None:
        self.model_path = self._resolve_model_path(model_path)
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.trust_remote_code = trust_remote_code
        self._model = None
        self._tokenizer = None
        self._processor = None
        if load_on_init:
            self.load()

    @staticmethod
    def _resolve_model_path(model_path: str) -> str:
        path = Path(model_path)
        if path.exists() and path.is_dir():
            snapshots = path / "snapshots"
            if snapshots.exists():
                snapshot_dirs = sorted([p for p in snapshots.iterdir() if p.is_dir()])
                if snapshot_dirs:
                    return str(snapshot_dirs[-1])
        return str(path)

    @property
    def is_available(self) -> bool:
        if not Path(self.model_path).exists():
            return False
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
        except ImportError:
            return False
        return True

    def load(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        if not Path(self.model_path).exists():
            raise RuntimeError(f"本地模型目录不存在: {self.model_path}")
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("未安装 transformers/torch，无法加载本地 Qwen 模型") from exc

        dtype: Optional[object]
        if self.torch_dtype == "auto":
            dtype = "auto"
        else:
            dtype = getattr(torch, self.torch_dtype)

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=self.trust_remote_code,
        )
        try:
            from transformers import AutoProcessor

            self._processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=self.trust_remote_code,
            )
        except Exception:
            self._processor = None
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=dtype,
            device_map=self.device_map,
            trust_remote_code=self.trust_remote_code,
        )

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        self.load()
        import torch

        assert self._model is not None
        assert self._tokenizer is not None

        inputs = self._tokenizer(prompt, return_tensors="pt")
        device = getattr(self._model, "device", None)
        if device is not None:
            inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0.0,
                temperature=max(temperature, 1e-5),
                pad_token_id=self._tokenizer.eos_token_id,
            )

        prompt_length = inputs["input_ids"].shape[-1]
        completion = outputs[0][prompt_length:]
        return self._tokenizer.decode(completion, skip_special_tokens=True).strip()

    def generate_multimodal(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> str:
        """
        本地多模态推理入口。

        说明：
        - 优先尝试 processor/chat-template 的原生路径；
        - 若当前 transformers/模型不支持该路径，则回退到文本融合兜底，保证链路可运行。
        """
        self.load()
        import torch

        assert self._model is not None
        assert self._tokenizer is not None

        native_prompt = self._build_native_prompt(messages)
        if self._processor is not None and hasattr(self._processor, "apply_chat_template"):
            try:
                native_prompt = self._processor.apply_chat_template(
                    list(messages),
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                # 部分模型 chat template 不兼容时，降级到我们自己的融合模板
                pass

        inputs = self._tokenizer(native_prompt, return_tensors="pt")
        device = getattr(self._model, "device", None)
        if device is not None:
            inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0.0,
                temperature=max(temperature, 1e-5),
                pad_token_id=self._tokenizer.eos_token_id,
            )
        prompt_length = inputs["input_ids"].shape[-1]
        completion = outputs[0][prompt_length:]
        return self._tokenizer.decode(completion, skip_special_tokens=True).strip()

    @staticmethod
    def _build_native_prompt(messages: Sequence[Mapping[str, Any]]) -> str:
        """把多模态消息折叠为稳健的文本模板（兜底路径）。"""
        lines = ["你将收到多模态上下文，请仅输出 JSON 结果。"]
        for idx, message in enumerate(messages):
            role = str(message.get("role", "user"))
            content = message.get("content", "")
            lines.append(f"[{idx}] role={role}")
            if isinstance(content, str):
                lines.append(content)
                continue
            if not isinstance(content, list):
                lines.append(str(content))
                continue
            for item in content:
                if isinstance(item, str):
                    lines.append(f"- text: {item}")
                    continue
                if not isinstance(item, dict):
                    lines.append(f"- item: {json.dumps(item, ensure_ascii=False)}")
                    continue
                if "text" in item:
                    lines.append(f"- text: {item['text']}")
                elif "image" in item:
                    lines.append(f"- image: {item['image']}")
                elif "audio" in item:
                    lines.append(f"- audio: {item['audio']}")
                elif "video" in item:
                    lines.append(f"- video: {item['video']}")
                elif item.get("type") == "text":
                    lines.append(f"- text: {item.get('text', '')}")
                elif item.get("type") == "image":
                    lines.append(f"- image: {item.get('image', item.get('path', ''))}")
                elif item.get("type") == "audio":
                    lines.append(f"- audio: {item.get('audio', item.get('path', ''))}")
                elif item.get("type") == "video":
                    lines.append(f"- video: {item.get('video', item.get('path', ''))}")
                else:
                    lines.append(f"- item: {json.dumps(item, ensure_ascii=False)}")
        return "\n".join(lines)

