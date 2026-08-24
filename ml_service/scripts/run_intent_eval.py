"""
run_intent_eval.py
==================
对意图识别模块运行 7×16 矩阵评测，输出 precision/recall/F1 报告。

使用方式：
  python scripts/run_intent_eval.py
  python scripts/run_intent_eval.py --output knowledge_graph/processed_data/intent_eval_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intent_recognizer.analyzer import IntentAnalyzer
from intent_recognizer.evaluator import IntentEvaluator
from intent_recognizer.schema import IntentInput


def compute_prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description="意图识别 7×16 矩阵评测")
    parser.add_argument("--output", default=str(
        PROJECT_ROOT / "knowledge_graph" / "processed_data" / "intent_eval_report.json"
    ))
    parser.add_argument("--no-llm", action="store_true",
                        help="不调用 LLM，仅用规则+线索做评测（快速冒烟）")
    args = parser.parse_args()

    evaluator = IntentEvaluator()
    records = evaluator.get_eval_records()
    print(f"评测集总条数: {len(records)}")

    analyzer = IntentAnalyzer(llm=None) if args.no_llm else IntentAnalyzer()

    # 按主类和风险阶段统计 TP/FP/FN
    cat_tp: dict = defaultdict(int)
    cat_fp: dict = defaultdict(int)
    cat_fn: dict = defaultdict(int)
    stage_tp: dict = defaultdict(int)
    stage_fp: dict = defaultdict(int)
    stage_fn: dict = defaultdict(int)
    details = []

    for record in records:
        intent_input = IntentInput(
            query=record.query,
            image_ocr_text=record.image_ocr_text or "",
            image_caption=record.image_caption or "",
            audio_text=record.audio_text or "",
            audio_deepfake_score=record.audio_deepfake_score,
        )
        result = analyzer.analyze(intent_input)

        pred_cat = result.coarse_category
        true_cat = record.coarse_category
        pred_stage = result.risk_stage
        true_stage = record.risk_stage

        # 主类统计
        if pred_cat == true_cat:
            cat_tp[true_cat] += 1
        else:
            cat_fp[pred_cat] += 1
            cat_fn[true_cat] += 1

        # 风险阶段统计
        if pred_stage == true_stage:
            stage_tp[true_stage] += 1
        else:
            stage_fp[pred_stage] += 1
            stage_fn[true_stage] += 1

        details.append({
            "query": record.query[:80],
            "true_cat": true_cat,
            "pred_cat": pred_cat,
            "true_stage": true_stage,
            "pred_stage": pred_stage,
            "cat_correct": pred_cat == true_cat,
            "stage_correct": pred_stage == true_stage,
        })

    # 汇总各主类 PRF
    all_cats = sorted(set(list(cat_tp.keys()) + list(cat_fp.keys()) + list(cat_fn.keys())))
    cat_report = {}
    for cat in all_cats:
        cat_report[cat] = compute_prf(cat_tp[cat], cat_fp[cat], cat_fn[cat])

    # 汇总各风险阶段 PRF
    all_stages = sorted(set(list(stage_tp.keys()) + list(stage_fp.keys()) + list(stage_fn.keys())))
    stage_report = {}
    for stage in all_stages:
        stage_report[stage] = compute_prf(stage_tp[stage], stage_fp[stage], stage_fn[stage])

    # 宏平均
    macro_cat_f1 = round(sum(v["f1"] for v in cat_report.values()) / max(len(cat_report), 1), 4)
    macro_stage_f1 = round(sum(v["f1"] for v in stage_report.values()) / max(len(stage_report), 1), 4)

    report = {
        "total": len(records),
        "macro_category_f1": macro_cat_f1,
        "macro_stage_f1": macro_stage_f1,
        "category_report": cat_report,
        "stage_report": stage_report,
        "records": details,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n宏平均主类 F1: {macro_cat_f1}")
    print(f"宏平均风险阶段 F1: {macro_stage_f1}")
    print(f"报告已写入: {output_path}")


if __name__ == "__main__":
    main()
