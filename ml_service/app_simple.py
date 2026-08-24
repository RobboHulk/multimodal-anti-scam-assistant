"""简化版 ML 服务入口 — 直接调用 DashScope qwen3.5-omni-plus 实现多模态防御分析。

使用 OpenAI 兼容方式调用（Qwen-Omni 系列仅支持此方式）。
模型输出纯自然语言/Markdown 格式，前端直接渲染。
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from openai import OpenAI

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"), override=True)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL_NAME = os.getenv("ANTIFRAUD_MODEL", "qwen3.5-omni-plus")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

client: Optional[OpenAI] = None
if DASHSCOPE_API_KEY:
    client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL, timeout=120.0)


# ═══════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════

class UserProfilePayload(BaseModel):
    id: Optional[int] = None
    username: str = ""
    ageGroup: Optional[int] = None
    gender: Optional[int] = None
    occupation: str = ""
    riskPreference: Optional[int] = None
    riskThreshold: Optional[float] = None
    interventionStrategy: Optional[int] = None


class ChatRequest(BaseModel):
    text: str = ""
    session_id: str = "default"
    userProfile: Optional[UserProfilePayload] = None
    image_path: Optional[str] = ""
    audio_path: Optional[str] = ""
    video_path: Optional[str] = ""
    dimensions: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    chatType: int = 0
    riskScore: float = 0.0
    scamType: str = ""
    confidence: float = 0.0
    riskAction: str = ""
    tags: List[str] = Field(default_factory=list)
    chatResponse: str = ""


# ═══════════════════════════════════════════════════════════════
# 会话历史（内存存储，重启清空）
# ═══════════════════════════════════════════════════════════════

_session_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
MAX_HISTORY_TURNS = 10


# ═══════════════════════════════════════════════════════════════
# 系统提示词
# ═══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """# 角色设定

你是一个多模态内容安全分析智能体，服务于反电信诈骗安全研判系统。你的核心使命是保护用户免受诈骗、网络钓鱼、社工攻击、深度伪造等威胁。

## 能力范围

1. **文本语义分析** — 识别诈骗话术（冒充公检法、虚假投资、杀猪盘、刷单返利、假冒客服）、心理操控手法（紧迫感、权威冒充、恐惧诱导）、隐私信息套取行为
2. **图片鉴别** — 检测AI生成图片、P图痕迹、伪造证件/截图/转账记录、OCR识别图中关键文字
3. **音频检测** — 识别AI语音合成/克隆痕迹、分析通话内容中的社工话术
4. **视频检测** — 深度伪造换脸检测、口型同步性分析、AI生成视频特征识别
5. **链接/二维码分析** — 域名仿冒识别、钓鱼页面特征、恶意短链接
6. **多模态交叉验证** — 文本与图片一致性校验、音视频匹配度分析

## 输出要求

- **格式**：使用 Markdown（标题、加粗、列表、引用）。禁止输出 JSON 或代码块
- **结构**：
  1. 一句话核心结论（标注风险等级：🟢安全 / 🟡可疑 / 🔴高危）
  2. 关键发现（分点列出具体证据）
  3. 安全建议（具体、可操作的行动指引）
- **简洁原则**：内容无风险时一两句话确认即可，不要过度分析。只在有真实风险信号时展开详细分析
- **语气**：专业平实，不冰冷也不过度恐吓。高危时语气坚决

## 分析原则

- 基于证据研判，不做无依据推测
- 多维度证据交叉印证提升可信度
- 对紧急高危情况，优先建议「立即停止交互+报警」
- 始终站在保护用户的立场
- 承认分析局限性，证据不足时如实说明

## 对话规范

- 用户发送日常问候时正常回应，不必强行进行安全分析
- 用户询问安全知识时提供专业科普
- 收到多模态内容（图片/音频/视频）时自动启动安全研判
- 保持对话连贯性，记住上下文
"""


_uploaded_file_cache: Dict[str, str] = {}


def _upload_local_file(file_path: str) -> str:
    """将本地文件或 localhost URL 上传到 DashScope OSS，返回可访问 URL。"""
    if not file_path or not file_path.strip():
        return ""

    path = file_path.strip().replace("\\", "/")

    # 如果是公网 URL（非 localhost），直接返回
    if path.startswith(("http://", "https://")):
        # localhost URL 需要下载后再上传到 OSS
        if "localhost" in path or "127.0.0.1" in path:
            return _download_and_upload_to_oss(path)
        return path

    if path in _uploaded_file_cache:
        return _uploaded_file_cache[path]

    if not os.path.isfile(path):
        alt_paths = [
            path,
            os.path.join("/app/uploads", os.path.basename(path)),
            os.path.join("./uploads", os.path.basename(path)),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "uploads", os.path.basename(path)),
        ]
        found = None
        for p in alt_paths:
            if os.path.isfile(p):
                found = p
                break
        if not found:
            return path
        path = found

    return _upload_file_to_oss(path)


def _download_and_upload_to_oss(url: str) -> str:
    """从 localhost URL 下载文件并上传到 DashScope OSS。"""
    import tempfile
    import requests
    from urllib.parse import urlparse

    if url in _uploaded_file_cache:
        return _uploaded_file_cache[url]

    try:
        # 下载文件到临时目录
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        # 从 URL 提取文件扩展名
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        suffix = os.path.splitext(filename)[1] or ".bin"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name
        
        # 上传到 OSS
        oss_url = _upload_file_to_oss(tmp_path)
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if oss_url and oss_url != tmp_path:
            _uploaded_file_cache[url] = oss_url
            return oss_url
        
        return url
    except Exception as e:
        print(f"[ML] 下载文件失败: {url}, error: {e}")
        return url


def _upload_file_to_oss(local_path: str) -> str:
    """将本地文件上传到 DashScope OSS。"""
    if local_path in _uploaded_file_cache:
        return _uploaded_file_cache[local_path]
    
    try:
        import dashscope
        dashscope.api_key = DASHSCOPE_API_KEY
        from dashscope import Files

        response = Files.upload(file_path=local_path, purpose="file-extract", api_key=DASHSCOPE_API_KEY)
        if response.status_code == 200:
            uploaded_files = (response.output or {}).get("uploaded_files") or []
            if uploaded_files:
                file_id = uploaded_files[0].get("file_id", "")
                if file_id:
                    detail = Files.get(file_id, api_key=DASHSCOPE_API_KEY)
                    if detail.status_code == 200:
                        url = (detail.output or {}).get("url", "")
                        if url:
                            _uploaded_file_cache[local_path] = url
                            return url
    except Exception as e:
        print(f"[ML] 上传到 OSS 失败: {local_path}, error: {e}")

    from pathlib import Path
    return Path(local_path).resolve().as_uri()


def _build_user_content(request: ChatRequest) -> List[Dict[str, Any]]:
    """根据请求构建 OpenAI 兼容的 content 列表。"""
    content: List[Dict[str, Any]] = []

    if request.image_path:
        url = _upload_local_file(request.image_path)
        if url:
            content.append({"type": "image_url", "image_url": {"url": url}})

    if request.audio_path:
        url = _upload_local_file(request.audio_path)
        if url:
            fmt = "wav"
            lower = request.audio_path.lower()
            if lower.endswith(".mp3"):
                fmt = "mp3"
            elif lower.endswith(".flac"):
                fmt = "flac"
            content.append({"type": "input_audio", "input_audio": {"data": url, "format": fmt}})

    if request.video_path:
        url = _upload_local_file(request.video_path)
        if url:
            content.append({"type": "video_url", "video_url": {"url": url}})

    text_parts = []
    if request.text:
        text_parts.append(request.text)
    if request.userProfile:
        profile = request.userProfile
        profile_desc = f"[用户画像] 年龄段:{profile.ageGroup}, 性别:{profile.gender}, 职业:{profile.occupation}, 风险偏好:{profile.riskPreference}"
        text_parts.append(profile_desc)

    if request.dimensions:
        dims_str = ", ".join(request.dimensions)
        text_parts.append(f"[启用的检测维度] {dims_str}")

    if text_parts:
        content.append({"type": "text", "text": "\n".join(text_parts)})

    if not content:
        content.append({"type": "text", "text": "你好"})

    return content


def _call_model(request: ChatRequest) -> ChatResponse:
    """调用 qwen3.5-omni-plus 并解析结果。"""
    if not client:
        return ChatResponse(
            chatType=0,
            chatResponse="ML 服务未配置 DASHSCOPE_API_KEY，无法进行分析。",
        )

    session_id = request.session_id or "default"
    history = _session_store[session_id]

    user_content = _build_user_content(request)

    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-(MAX_HISTORY_TURNS * 2):]:
        messages.append(turn)
    messages.append({"role": "user", "content": user_content})

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            modalities=["text"],
            stream=True,
            stream_options={"include_usage": True},
        )

        full_text = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content

    except Exception as e:
        return ChatResponse(
            chatType=0,
            chatResponse=f"模型调用出错: {str(e)[:200]}",
        )

    # 保存对话历史
    history.append({"role": "user", "content": user_content})
    history.append({"role": "assistant", "content": full_text})
    if len(history) > MAX_HISTORY_TURNS * 2:
        _session_store[session_id] = history[-(MAX_HISTORY_TURNS * 2):]

    # 去掉 <think> 标签，直接返回纯文本
    clean_text = re.sub(r"<think>[\s\S]*?</think>", "", full_text).strip()
    return ChatResponse(
        chatType=0,
        riskScore=0.0,
        scamType="",
        confidence=0.0,
        riskAction="",
        tags=[],
        chatResponse=clean_text or full_text[:500],
    )


# ═══════════════════════════════════════════════════════════════
# FastAPI 路由
# ═══════════════════════════════════════════════════════════════

app = FastAPI(title="Multimodal Anti-Fraud ML Service (Simple)", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/api/chat/send", response_model=ChatResponse)
def chat_send(request: ChatRequest) -> ChatResponse:
    return _call_model(request)


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    """SSE 流式端点：先返回思考过程，再返回最终 JSON 结果。"""
    import asyncio

    def generate():
        if not client:
            yield f"data: {json.dumps({'type': 'error', 'content': 'ML 服务未配置 API KEY'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        session_id = request.session_id or "default"
        history = _session_store[session_id]
        user_content = _build_user_content(request)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history[-(MAX_HISTORY_TURNS * 2):]:
            messages.append(turn)
        messages.append({"role": "user", "content": user_content})

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                modalities=["text"],
                stream=True,
                stream_options={"include_usage": True},
            )

            full_text = ""
            thinking_text = ""
            in_thinking = False
            thinking_done = False

            for chunk in completion:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = delta.content or ""

                if not content:
                    continue

                full_text += content

                # 检测 <think> 标签（Qwen3 思考模式的输出格式）
                if "<think>" in full_text and not in_thinking and not thinking_done:
                    in_thinking = True
                    # 提取 <think> 之后的内容
                    idx = full_text.index("<think>") + len("<think>")
                    thinking_text = full_text[idx:]
                    yield f"data: {json.dumps({'type': 'thinking_start'}, ensure_ascii=False)}\n\n"
                    if thinking_text:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': thinking_text}, ensure_ascii=False)}\n\n"
                    continue

                if in_thinking:
                    if "</think>" in content:
                        # 思考结束
                        parts = content.split("</think>", 1)
                        if parts[0]:
                            thinking_text += parts[0]
                            yield f"data: {json.dumps({'type': 'thinking', 'content': parts[0]}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'thinking_end'}, ensure_ascii=False)}\n\n"
                        in_thinking = False
                        thinking_done = True
                        # </think> 之后的内容是正式回复
                        if len(parts) > 1 and parts[1]:
                            yield f"data: {json.dumps({'type': 'content', 'content': parts[1]}, ensure_ascii=False)}\n\n"
                    else:
                        thinking_text += content
                        yield f"data: {json.dumps({'type': 'thinking', 'content': content}, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)[:200]}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 保存对话历史
        history.append({"role": "user", "content": user_content})
        history.append({"role": "assistant", "content": full_text})
        if len(history) > MAX_HISTORY_TURNS * 2:
            _session_store[session_id] = history[-(MAX_HISTORY_TURNS * 2):]

        # 去掉 <think>...</think>，直接返回纯文本
        clean_text = re.sub(r"<think>[\s\S]*?</think>", "", full_text).strip()
        result_data = {
            "chatType": 0,
            "riskScore": 0.0,
            "scamType": "",
            "confidence": 0.0,
            "riskAction": "",
            "tags": [],
            "chatResponse": clean_text or full_text[:500],
        }
        yield f"data: {json.dumps({'type': 'result', 'data': result_data}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

