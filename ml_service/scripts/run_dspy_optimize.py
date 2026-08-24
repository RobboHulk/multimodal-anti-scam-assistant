"""
run_dspy_optimize.py
====================
使用 DSPy MIPROv2 对意图识别 Prompt 进行自动优化。
"""
from __future__ import annotations

import argparse
import json
import os
import pprint
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intent_recognizer.dspy_optimizer import IntentDSPyOptimizer
from intent_recognizer.evaluator import IntentEvalRecord, IntentEvaluator


def load_eval_records(eval_path: Path) -> list[IntentEvalRecord]:
    records = []
    if eval_path.suffix.lower() == ".jsonl":
        with open(eval_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(IntentEvalRecord(**json.loads(line)))
        return records

    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("records", [])
    for item in items:
        records.append(
            IntentEvalRecord(
                query=item.get("query", ""),
                image_ocr_text=item.get("image_ocr_text", ""),
                image_caption=item.get("image_caption", ""),
                audio_text=item.get("audio_text", ""),
                audio_deepfake_score=item.get("audio_deepfake_score"),
                is_fraud_relevant=item.get("is_fraud_relevant", False),
                coarse_category=item.get("coarse_category", "OTHER_UNKNOWN"),
                risk_stage=item.get("risk_stage", "S0"),
                recommended_action=item.get("recommended_action", "educate"),
            )
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="DSPy MIPROv2 意图识别 Prompt 优化")
    parser.add_argument("--eval-path", default=None, help="评测集路径（支持 JSON/JSONL）")
    parser.add_argument("--train-size", type=int, default=80)
    parser.add_argument("--val-size", type=int, default=20)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    output_path = args.output or str(
        PROJECT_ROOT / "knowledge_graph" / "processed_data" / "dspy_optimized_prompt.json"
    )

    if args.eval_path:
        all_records = load_eval_records(Path(args.eval_path))
    else:
        evaluator = IntentEvaluator(IntentAnalyzer(enable_llm=False))
        all_records = evaluator.get_eval_records()

    train_records = all_records[: args.train_size]
    val_records = all_records[args.train_size: args.train_size + args.val_size]
    print(f"训练集: {len(train_records)} 条，验证集: {len(val_records)} 条")

    optimizer = IntentDSPyOptimizer()
    result = optimizer.optimize(
        train_records=train_records,
        val_records=val_records,
        output_path=output_path,
    )

    artifact = result["artifact"]
    few_shot_path = PROJECT_ROOT / "intent_recognizer" / "few_shot_examples.py"
    if result["status"] in {"ok", "fallback_no_dspy", "fallback_no_api_key"}:
        demos = artifact.get("demos", [])[:4]
        shallow_demo = demos[:2]
        deep_demo = demos[2:4] if len(demos) >= 4 else demos[:2]
        shallow_entries = []
        for idx, demo in enumerate(shallow_demo, 1):
            inp = demo.get("input", {})
            out = demo.get("output", {})
            shallow_entries.append({
                "label": f"自动优化示例{idx}",
                "input_summary": (
                    f"用户输入：'{inp.get('query','')}'\\n"
                    f"图像OCR：{inp.get('image_ocr_text','无') or '无'}\\n"
                    f"音频ASR：{inp.get('audio_text','无') or '无'}"
                ),
                "output": {
                    "is_fraud_relevant": out.get("is_fraud_relevant", False),
                    "coarse_category": out.get("coarse_category", "OTHER_UNKNOWN"),
                    "confidence": 0.9,
                    "reasoning": f"基于优化产物导出的示例，风险阶段={out.get('risk_stage', 'S0')}。",
                },
            })
        deep_entries = []
        for idx, demo in enumerate(deep_demo, 1):
            inp = demo.get("input", {})
            out = demo.get("output", {})
            deep_entries.append({
                "label": f"自动优化深度示例{idx}",
                "input_summary": (
                    f"用户输入：'{inp.get('query','')}'\\n"
                    f"浅层初判：{out.get('coarse_category', 'OTHER_UNKNOWN')}, confidence=0.90\\n"
                    f"线索：risk_stage={out.get('risk_stage','S0')}"
                ),
                "output": {
                    "is_fraud_relevant": out.get("is_fraud_relevant", False),
                    "coarse_category": out.get("coarse_category", "OTHER_UNKNOWN"),
                    "risk_stage": out.get("risk_stage", "S0"),
                    "recommended_action": out.get("recommended_action", "educate"),
                    "primary_signals": ["优化产物示例"],
                    "missing_evidence": ["完整上下文"],
                    "clarifying_questions": ["是否还有更多上下文截图或录音？"],
                    "confidence": 0.9,
                    "reasoning": "1. 关键证据：来自自动优化示例。2. 类型：依据产物标签。3. 阶段：依据产物标签。",
                },
            })
        content = (
            '"""\n'
            'few_shot_examples.py\n'
            '====================\n'
            'SHALLOW / DEEP Prompt 的 few-shot 示例库。\n'
            '由 scripts/run_dspy_optimize.py 自动更新。\n'
            '"""\n'
            'from __future__ import annotations\n\n'
            'from typing import Any, Dict, List\n\n'
            f'SHALLOW_FEW_SHOT: List[Dict[str, Any]] = {pprint.pformat(shallow_entries, width=100, sort_dicts=False)}\n\n'
            f'DEEP_FEW_SHOT: List[Dict[str, Any]] = {pprint.pformat(deep_entries, width=100, sort_dicts=False)}\n\n'
            'def format_shallow_few_shot() -> str:\n'
            '    """返回 SHALLOW Prompt 用的 few-shot 文本块。"""\n'
            '    lines = ["## 示例（仅供参考，不要照抄）"]\n'
            '    for ex in SHALLOW_FEW_SHOT:\n'
            '        lines.append(f"\\n### {ex[\'label\']}")\n'
            '        lines.append(f"输入摘要: {ex[\'input_summary\']}")\n'
            '        lines.append(f"期望输出: {ex[\'output\']}")\n'
            '    return "\\n".join(lines)\n\n'
            'def format_deep_few_shot() -> str:\n'
            '    """返回 DEEP Prompt 用的 few-shot 文本块。"""\n'
            '    import json\n'
            '    lines = ["## 示例（仅供参考，不要照抄）"]\n'
            '    for ex in DEEP_FEW_SHOT:\n'
            '        lines.append(f"\\n### {ex[\'label\']}")\n'
            '        lines.append(f"输入摘要: {ex[\'input_summary\']}")\n'
            '        lines.append(f"期望输出:\\n{json.dumps(ex[\'output\'], ensure_ascii=False, indent=2)}")\n'
            '    return "\\n".join(lines)\n'
        )
        few_shot_path.write_text(content, encoding="utf-8")

    print(f"优化完成: status={result['status']}, score={artifact.get('score', 0):.4f}")
    print(f"产物路径: {output_path}")
    print(f"few-shot 更新: {few_shot_path}")


from intent_recognizer.analyzer import IntentAnalyzer

if __name__ == "__main__":
    main()
