"""
auto_label_risk_stage.py
========================
使用 DashScope qwen-plus 对 external_converted.jsonl 自动标注 risk_stage。
输出：
- intent_recognizer/data/auto_labeled.jsonl
- intent_recognizer/data/needs_review.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

from dashscope import Generation

from shared.config.llm_config import DEFAULT_DASHSCOPE_MODEL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "intent_recognizer" / "data" / "external_converted.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "intent_recognizer" / "data" / "auto_labeled.jsonl"
REVIEW_PATH = PROJECT_ROOT / "intent_recognizer" / "data" / "needs_review.jsonl"

STAGE_DEFINITIONS = {
    "S0": "无风险，日常对话",
    "S1": "初步接触，对方开始建立联系或信任",
    "S2": "诱导深入，要求提供信息或下载软件",
    "S3": "施压操控，制造紧迫感或恐惧",
    "S4": "资金操作，诱导转账/付款/充值",
    "S5": "损失已发生，资金已转出",
    "S6": "二次受害，以追损为名再次诈骗",
}

FEW_SHOT = [
    {
        "query": "你好，今天上海天气怎么样？",
        "label": {"risk_stage": "S0", "confidence": 0.99, "reason": "纯日常闲聊。"},
    },
    {
        "query": "有人加我微信说是客服，问我要手机号和验证码。",
        "label": {"risk_stage": "S2", "confidence": 0.91, "reason": "已开始索要个人信息和验证码。"},
    },
    {
        "query": "对方让我把钱转到安全账户配合调查。",
        "label": {"risk_stage": "S4", "confidence": 0.97, "reason": "已进入明确资金转移阶段。"},
    },
]


def build_prompt(query: str, coarse_category: str, is_fraud_relevant: bool) -> str:
    return f"""你是中文反诈风险阶段标注器。请根据用户输入判断其所处风险阶段 S0-S6，并输出 JSON。

风险阶段定义：
{json.dumps(STAGE_DEFINITIONS, ensure_ascii=False, indent=2)}

Few-shot 示例：
{json.dumps(FEW_SHOT, ensure_ascii=False, indent=2)}

当前样本：
- query: {query}
- coarse_category: {coarse_category}
- is_fraud_relevant: {is_fraud_relevant}

输出格式：
{{
  "risk_stage": "S0-S6",
  "confidence": 0.0-1.0,
  "reason": "简短中文理由"
}}

只输出 JSON，不要其他内容。"""


def call_llm(prompt: str) -> Dict:
    response = Generation.call(
        model=DEFAULT_DASHSCOPE_MODEL,
        prompt=prompt,
        temperature=0.1,
        result_format="message",
    )
    if response.status_code != 200:
        raise RuntimeError(f"Generation error: {response.code} {response.message}")
    content = response.output.choices[0].message.content
    if isinstance(content, list):
        content = content[0].get("text", "")
    text = str(content).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def load_done(input_path: Path) -> set[str]:
    if not input_path.exists():
        return set()
    done = set()
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = f"{item.get('source_dataset','')}::{item.get('query','')[:120]}"
            done.add(key)
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description="自动标注 risk_stage")
    parser.add_argument("--input", default=str(INPUT_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--review", default=str(REVIEW_PATH))
    parser.add_argument("--max-samples", type=int, default=2000)
    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        raise RuntimeError("未设置 DASHSCOPE_API_KEY")

    input_path = Path(args.input)
    output_path = Path(args.output)
    review_path = Path(args.review)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    done = load_done(output_path)
    total = 0
    labeled = 0
    review_count = 0

    with open(input_path, "r", encoding="utf-8") as f, \
         open(output_path, "a", encoding="utf-8") as out, \
         open(review_path, "a", encoding="utf-8") as review_out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            key = f"{item.get('source_dataset','')}::{item.get('query','')[:120]}"
            if key in done:
                continue
            total += 1
            if total > args.max_samples:
                break

            prompt = build_prompt(
                query=item.get("query", ""),
                coarse_category=item.get("coarse_category", "OTHER_UNKNOWN"),
                is_fraud_relevant=item.get("is_fraud_relevant", False),
            )
            result = call_llm(prompt)
            item["risk_stage"] = result.get("risk_stage", "S1")
            item["risk_stage_confidence"] = float(result.get("confidence", 0.0))
            item["risk_stage_reason"] = result.get("reason", "")
            out.write(json.dumps(item, ensure_ascii=False) + "\n")
            labeled += 1

            if item["risk_stage_confidence"] < 0.75:
                review_out.write(json.dumps(item, ensure_ascii=False) + "\n")
                review_count += 1

            if labeled % 50 == 0:
                print(f"[{labeled}] 已标注，待人工复核: {review_count}", flush=True)

    print(f"\n标注完成: {labeled} 条")
    print(f"低置信度待复核: {review_count} 条 -> {review_path}")
    print(f"输出: {output_path}")


if __name__ == "__main__":
    main()
