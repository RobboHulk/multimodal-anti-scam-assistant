"""意图识别 Prompt 模板。"""

from __future__ import annotations

import json

from intent_recognizer.schema import CueSet, IntentInput
from knowledge_graph.scam_type_taxonomy import PRIMARY_SCAM_TYPES


INTENT_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["is_fraud_relevant", "coarse_category", "risk_stage", "recommended_action", "reasoning"],
    "properties": {
        "is_fraud_relevant": {"type": "boolean"},
        "intent": {
            "type": "string",
            "enum": ["GENERAL_CHAT", "RISK_CHECK", "EVIDENCE_LOOKUP", "SAFETY_GUIDANCE"],
        },
        "coarse_category": {
            "type": "string",
            "enum": list(PRIMARY_SCAM_TYPES.keys()),
        },
        "risk_stage": {
            "type": "string",
            "enum": ["S0", "S1", "S2", "S3", "S4", "S5", "S6"],
        },
        "recommended_action": {
            "type": "string",
            "enum": ["educate", "verify", "warn", "block", "report"],
        },
        "primary_signals": {"type": "array", "items": {"type": "string"}},
        "missing_evidence": {"type": "array", "items": {"type": "string"}},
        "clarifying_questions": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
}


def format_cues(cues: CueSet) -> str:
    lines = [
        f"- inferred_scam_type: {cues.inferred_scam_type}",
        f"- tactic_tags: {', '.join(cues.tactic_tags) or '无'}",
        f"- cue_density_score: {cues.cue_density_score}",
        f"- cross_modal_matches: {', '.join(cues.cross_modal_matches) or '无'}",
        f"- entities: {json.dumps(cues.entities[:8], ensure_ascii=False)}",
    ]
    cue_items = cues.all_cues()[:20]
    if cue_items:
        lines.append("- top_cues:")
        for cue in cue_items:
            lines.append(
                f"  - source={cue.source}, type={cue.cue_type}, text={cue.text}, weight={cue.weight}"
            )
    return "\n".join(lines)


def build_intent_prompt(intent_input: IntentInput, cues: CueSet, memory_summary: str) -> str:
    type_enum = "\n".join([f"- {key}: {value}" for key, value in PRIMARY_SCAM_TYPES.items()])
    schema_text = json.dumps(INTENT_OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    history = memory_summary or "无"
    return f"""你是一个专业的多模态反诈意图分析器，请根据输入线索进行结构化判断。

请严格按以下顺序思考：
1. 判断是否与诈骗相关。
2. 如果相关，从给定诈骗大类中选择最匹配的一类。
3. 判断所处风险阶段 S0-S6。
4. 给出处置建议。
5. 提炼关键证据、缺失证据与追问问题。

你必须只输出 JSON，不要输出解释文字，不要输出 Markdown。

## 当前用户输入
{intent_input.text}

## 图像线索
OCR: {intent_input.image_ocr_text or '无'}
Caption: {intent_input.image_caption or '无'}

## 音频线索
ASR: {intent_input.audio_text or '无'}
DeepfakeScore: {intent_input.audio_deepfake_score if intent_input.audio_deepfake_score is not None else '无'}

## 会话记忆摘要
{history}

## 已抽取线索
{format_cues(cues)}

## 诈骗类型候选
{type_enum}

## 输出 JSON Schema
{schema_text}
"""

