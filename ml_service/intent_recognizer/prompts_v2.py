"""智能提示工程（动态提示生成）。"""

from __future__ import annotations

import json
from typing import Any, Dict

from intent_recognizer.few_shot_examples import format_deep_few_shot, format_shallow_few_shot
from intent_recognizer.prompts import INTENT_OUTPUT_SCHEMA, format_cues
from intent_recognizer.schema import CueSet, IntentInput
from knowledge_graph.scam_type_taxonomy import PRIMARY_SCAM_TYPES

SHALLOW_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["is_fraud_relevant", "coarse_category", "confidence", "reasoning"],
    "properties": {
        "is_fraud_relevant": {"type": "boolean"},
        "coarse_category": {"type": "string", "enum": list(PRIMARY_SCAM_TYPES.keys())},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
}

PROMPT_TEMPLATES = {
    "shallow": {
        "default": "你是反诈系统的快速分流模块。请做一次低成本初判。\n\n任务目标：\n1. 判断是否与诈骗相关；\n2. 给出最可能诈骗大类（若无则 OTHER_UNKNOWN）；\n3. 给出置信度；\n4. 给出一句简短理由（填入 reasoning 字段，不超过 60 字）。\n\n约束：\n- 只输出 JSON；\n- 不要输出 Markdown；\n- 不要输出额外解释。",
        "financial": "你是反诈系统的快速分流模块，专注于金融诈骗检测。请做一次低成本初判。",
        "phishing": "你是反诈系统的快速分流模块，专注于钓鱼诈骗检测。请做一次低成本初判。",
        "identity": "你是反诈系统的快速分流模块，专注于身份诈骗检测。请做一次低成本初判。",
    },
    "deep": {
        "default": "你是专业的多模态反诈意图分析器，请进行深度分析并输出结构化结论。\n\n## 分析步骤（请在 reasoning 字段中按此顺序推理，不超过 150 字）\n1. 关键证据是什么？（列举最多 3 条）\n2. 最符合哪个诈骗类型？理由是什么？\n3. 当前风险阶段（S0-S6）的判断依据？\n然后输出完整 JSON。\n\n## 约束\n- 只输出 JSON；\n- 不要输出 Markdown；\n- 不要省略必填字段；\n- reasoning 字段必须包含上述三步推理。",
        "financial": "你是专业的金融诈骗分析专家，请进行深度分析并输出结构化结论。",
        "phishing": "你是专业的钓鱼诈骗分析专家，请进行深度分析并输出结构化结论。",
        "identity": "你是专业的身份诈骗分析专家，请进行深度分析并输出结构化结论。",
    },
}

TASK_TYPE_KEYWORDS = {
    "financial": ["投资", "理财", "股票", "基金", "银行", "转账", "汇款", "贷款", "信用卡", "账户"],
    "phishing": ["链接", "网址", "网站", "登录", "密码", "验证码", "钓鱼", "仿冒", "虚假网站"],
    "identity": ["身份证", "个人信息", "姓名", "电话", "住址", "身份证号", "隐私", "信息泄露"],
}


def _type_enum_text() -> str:
    return "\n".join([f"- {key}: {value}" for key, value in PRIMARY_SCAM_TYPES.items()])


def _video_context_text(intent_input: IntentInput) -> str:
    preprocessing = intent_input.context.get("preprocessing", {}) if isinstance(intent_input.context, dict) else {}
    video = preprocessing.get("video", {}) if isinstance(preprocessing, dict) else {}
    if not isinstance(video, dict) or not video:
        return "无"
    keyframes = video.get("keyframes", [])
    behaviors = video.get("behavior_sequence", [])
    frame_brief = []
    if isinstance(keyframes, list):
        for frame in keyframes[:4]:
            if isinstance(frame, dict):
                frame_brief.append(f"t={frame.get('time', '')}, page={frame.get('page_type', '')}, text={str(frame.get('ocr_text', ''))[:60]}")
    behavior_brief = [str(item) for item in behaviors[:6]] if isinstance(behaviors, list) else []
    return json.dumps({"keyframes": frame_brief, "behaviors": behavior_brief}, ensure_ascii=False)


def _detect_task_type(query: str) -> str:
    query_lower = query.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return task_type
    return "default"


def build_shallow_intent_prompt(intent_input: IntentInput, cues: CueSet, memory_summary: str) -> str:
    history = memory_summary or "无"
    schema_text = json.dumps(SHALLOW_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    few_shot_text = format_shallow_few_shot()
    task_type = _detect_task_type(intent_input.text)
    prompt_template = PROMPT_TEMPLATES["shallow"].get(task_type, PROMPT_TEMPLATES["shallow"]["default"])
    return f"""{prompt_template}

{few_shot_text}

---

用户输入: {intent_input.text}
图像线索 OCR: {intent_input.image_ocr_text or '无'}
图像线索 Caption: {intent_input.image_caption or '无'}
音频线索 ASR: {intent_input.audio_text or '无'}
音频 Deepfake 分数: {intent_input.audio_deepfake_score if intent_input.audio_deepfake_score is not None else '无'}
视频线索摘要: {_video_context_text(intent_input)}
会话记忆摘要: {history}

已抽取线索:
{format_cues(cues)}

诈骗类型候选:
{_type_enum_text()}

输出 JSON Schema:
{schema_text}
"""


def build_deep_intent_prompt(
    intent_input: IntentInput,
    cues: CueSet,
    memory_summary: str,
    *,
    shallow_result: Dict[str, Any] | None = None,
) -> str:
    history = memory_summary or "无"
    schema_text = json.dumps(INTENT_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    shallow_text = json.dumps(shallow_result or {}, ensure_ascii=False, indent=2)
    few_shot_text = format_deep_few_shot()
    task_type = _detect_task_type(intent_input.text)
    prompt_template = PROMPT_TEMPLATES["deep"].get(task_type, PROMPT_TEMPLATES["deep"]["default"])
    return f"""{prompt_template}

{few_shot_text}

---

用户输入: {intent_input.text}
图像线索 OCR: {intent_input.image_ocr_text or '无'}
图像线索 Caption: {intent_input.image_caption or '无'}
音频线索 ASR: {intent_input.audio_text or '无'}
音频 Deepfake 分数: {intent_input.audio_deepfake_score if intent_input.audio_deepfake_score is not None else '无'}
视频线索摘要: {_video_context_text(intent_input)}
会话记忆摘要: {history}

浅层初判结果:
{shallow_text}

已抽取线索:
{format_cues(cues)}

诈骗类型候选:
{_type_enum_text()}

输出 JSON Schema:
{schema_text}
"""


def get_prompt_template(analysis_type: str, task_type: str) -> str:
    return PROMPT_TEMPLATES.get(analysis_type, {}).get(task_type, PROMPT_TEMPLATES.get(analysis_type, {}).get("default", ""))


def add_prompt_template(analysis_type: str, task_type: str, template: str) -> None:
    if analysis_type not in PROMPT_TEMPLATES:
        PROMPT_TEMPLATES[analysis_type] = {}
    PROMPT_TEMPLATES[analysis_type][task_type] = template


def evaluate_prompt_effectiveness(prompt: str, response: str) -> Dict[str, float]:
    effectiveness_score = 0.0
    if "{" in response and "}" in response:
        effectiveness_score += 0.3
    required_fields = ["is_fraud_relevant", "coarse_category", "confidence", "reasoning"]
    for field in required_fields:
        if field in response:
            effectiveness_score += 0.15
    if "reasoning" in response and len(response) > 20:
        effectiveness_score += 0.1
    return {
        "effectiveness_score": min(effectiveness_score, 1.0),
        "prompt_length": float(len(prompt)),
        "response_length": float(len(response)),
    }
