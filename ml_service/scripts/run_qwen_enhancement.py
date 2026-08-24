#!/usr/bin/env python3
"""
run_qwen_enhancement.py
=======================
Qwen 图谱增强执行入口

模式：
  --mode full    全量（调用 API 处理未缓存条目，已缓存条目直接复用）
  --mode sample  抽样验证
  --mode mock    纯规则 Mock，不调用 API

用法：
  python scripts/run_qwen_enhancement.py --mode full --use-api
  python scripts/run_qwen_enhancement.py --mode mock
  python scripts/run_qwen_enhancement.py --skip-text --skip-image   # 仅重建图谱
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from knowledge_graph.graph_builder.qwen_annotation_pipeline import QwenTextAnnotationPipeline
from knowledge_graph.graph_builder.qwen_image_annotation_pipeline import QwenImageAnnotationPipeline
from knowledge_graph.graph_builder.neo4j_connector import Neo4jGraphBuilder
from knowledge_graph.graph_builder.rebuild_audit import generate_rebuild_audit


def run_text_annotation(args):
    print("\n" + "=" * 70)
    print("阶段 1/3: 文本标注")
    print("=" * 70)

    pipeline = QwenTextAnnotationPipeline(
        processed_data_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        output_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        cache_dir=str(PROJECT_ROOT / "knowledge_graph/annotation_cache"),
        version=args.version,
        max_workers=args.workers,
        cache_scope=args.cache_scope,
        annotation_run_id=args.annotation_run_id,
    )
    return pipeline.run(
        mode=args.mode,
        sample_size=args.text_sample_size,
        use_api=args.use_api,
        api_scope=args.text_api_scope,
    )


def run_image_annotation(args):
    print("\n" + "=" * 70)
    print("阶段 2/3: 图片标注")
    print("=" * 70)

    pipeline = QwenImageAnnotationPipeline(
        processed_data_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        output_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        cache_dir=str(PROJECT_ROOT / "knowledge_graph/annotation_cache"),
        version=args.version,
        cache_scope=args.cache_scope,
        annotation_run_id=args.annotation_run_id,
    )
    return pipeline.run(
        mode=args.mode,
        sample_size=args.image_sample_size,
        use_api=args.use_api,
        api_scope=args.image_api_scope,
    )


def run_graph_rebuild(args):
    print("\n" + "=" * 70)
    print("阶段 3/3: 图谱重建")
    print("=" * 70)

    builder = Neo4jGraphBuilder(
        processed_data_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        output_dir=str(PROJECT_ROOT / "knowledge_graph/cypher_scripts"),
        annotation_cache_dir=str(PROJECT_ROOT / "knowledge_graph/annotation_cache"),
        version=args.version,
        cache_scope=args.cache_scope,
        annotation_run_id=args.annotation_run_id,
        strict_run_id=args.strict_run_id,
    )
    return builder.build_graph(enhanced=True)


def generate_enhancement_report(args, text_report, image_report, graph_summary, audit_report):
    import json
    report = {
        "generated_at": datetime.now().isoformat(),
        "annotation_version": args.version,
        "cache_scope": args.cache_scope,
        "annotation_run_id": args.annotation_run_id,
        "summary": {
            "text_annotation": text_report.get("stats", {}),
            "image_annotation": image_report.get("stats", {}),
            "graph_rebuild": graph_summary,
        },
        "tactic_nodes_created": int((graph_summary or {}).get("node_counts", {}).get("Tactic", 0)),
        "image_evidence_nodes_created": int((graph_summary or {}).get("node_counts", {}).get("ImageEvidence", 0)),
        "rebuild_audit_file": audit_report.get("audit_file", ""),
        "consistency_checks": audit_report.get("consistency_checks", {}),
    }
    report_file = PROJECT_ROOT / "knowledge_graph/processed_data" / f"enhancement_report_{args.version}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, ensure_ascii=False, indent=2, fp=f)
    print(f"\n已生成增强汇总报告: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Qwen 图谱增强执行入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/run_qwen_enhancement.py --mode mock
  python scripts/run_qwen_enhancement.py --mode full --use-api
  python scripts/run_qwen_enhancement.py --skip-text --skip-image
        """,
    )
    parser.add_argument("--mode", choices=["full", "sample", "mock"], default="sample")
    parser.add_argument("--use-api", action="store_true")
    parser.add_argument("--version", default="v1.0.0")
    parser.add_argument("--text-sample-size", type=int, default=150)
    parser.add_argument("--image-sample-size", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--text-api-scope", choices=["all", "priority"], default="all")
    parser.add_argument("--image-api-scope", choices=["all", "priority"], default="all")
    parser.add_argument("--cache-scope", default="default")
    parser.add_argument("--annotation-run-id", default="")
    parser.add_argument("--strict-run-id", action="store_true")
    parser.add_argument("--skip-text", action="store_true")
    parser.add_argument("--skip-image", action="store_true")
    parser.add_argument("--skip-graph", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("Qwen 图谱增强执行器")
    print("=" * 70)
    print(f"  运行模式:  {args.mode}")
    print(f"  使用 API:  {args.use_api}")
    print(f"  版本:      {args.version}")
    print(f"  并发数:    {args.workers}")
    print(f"  文本范围:  {args.text_api_scope}")
    print(f"  图片范围:  {args.image_api_scope}")
    print(f"  缓存作用域: {args.cache_scope}")
    print("=" * 70)

    if not args.annotation_run_id:
        args.annotation_run_id = datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"  本次 annotation_run_id: {args.annotation_run_id}")

    # 严格模式：显式要求 API 时，必须具备凭证
    if args.use_api and not os.environ.get("DASHSCOPE_API_KEY"):
        raise SystemExit(
            "已指定 --use-api，但未设置 DASHSCOPE_API_KEY。\n"
            "请先执行：export DASHSCOPE_API_KEY='your-api-key'"
        )

    text_report = {}
    image_report = {}
    graph_summary = {}

    if not args.skip_text:
        text_report = run_text_annotation(args)
    else:
        print("\n跳过文本标注")

    if not args.skip_image:
        image_report = run_image_annotation(args)
    else:
        print("\n跳过图片标注")

    if not args.skip_graph:
        graph_summary = run_graph_rebuild(args)
    else:
        print("\n跳过图谱重建")

    audit_report = generate_rebuild_audit(
        processed_data_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        output_dir=str(PROJECT_ROOT / "knowledge_graph/processed_data"),
        version=args.version,
        cache_scope=args.cache_scope,
        annotation_run_id=args.annotation_run_id,
        graph_summary=graph_summary,
    )
    print(f"\n已生成重建审计报告: {audit_report.get('audit_file', '')}")

    generate_enhancement_report(args, text_report, image_report, graph_summary, audit_report)

    print("\n" + "=" * 70)
    print("增强流程完成！")
    print("=" * 70)
    print(f"\n产物:")
    print(f"  文本标注  -> knowledge_graph/processed_data/text_annotated_{args.version}.jsonl")
    print(f"  图片标注  -> knowledge_graph/processed_data/images_annotated_{args.version}.jsonl")
    print(f"  图谱脚本  -> knowledge_graph/cypher_scripts/build_graph_enhanced_{args.version}.cypher")
    print(f"  增强报告  -> knowledge_graph/processed_data/enhancement_report_{args.version}.json")


if __name__ == "__main__":
    main()
