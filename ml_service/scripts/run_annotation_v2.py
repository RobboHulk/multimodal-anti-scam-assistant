"""
run_annotation_v2.py
=====================
等待截图渲染完成后，以 v2.0.0 版本重新运行全量 Qwen-VL 标注。

使用方式：
  # 使用本地 Qwen2.5-Omni-7B（推荐，无 API 费用）
  python scripts/run_annotation_v2.py --use-local-model

  # 使用 DashScope API（需要设置 DASHSCOPE_API_KEY 环境变量）
  python scripts/run_annotation_v2.py --use-api

  # 先跑 30 张样本验证效果
  python scripts/run_annotation_v2.py --use-local-model --mode sample --sample-size 30
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_MODULE = "knowledge_graph.graph_builder.qwen_image_annotation_pipeline"


def check_screenshots_ready() -> tuple[int, int]:
    """检查截图渲染进度。"""
    output_dir = PROJECT_ROOT / "datasets" / "generated_screenshots"
    if not output_dir.exists():
        return 0, 0
    pngs = list(output_dir.glob("*.png"))
    return len(pngs), len(pngs)


def main():
    parser = argparse.ArgumentParser(description="v2.0.0 全量图片标注")
    parser.add_argument("--use-local-model", action="store_true",
                        help="使用本地 Qwen2.5-Omni-7B（推荐）")
    parser.add_argument("--use-api", action="store_true",
                        help="使用 DashScope API")
    parser.add_argument("--mode", choices=["full", "sample", "mock"], default="full")
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--workers", type=int, default=1,
                        help="API 并发线程数，仅对 --use-api 生效，建议 4~8")
    parser.add_argument("--local-model-path", default=None)
    args = parser.parse_args()

    if not args.use_local_model and not args.use_api:
        print("请指定 --use-local-model 或 --use-api")
        sys.exit(1)

    # 检查截图数量
    png_count, _ = check_screenshots_ready()
    print(f"当前 generated_screenshots/ 中有 {png_count} 张 PNG")
    if png_count < 100 and args.mode == "full":
        print("[WARN] 截图数量较少，建议先等待 render_html_screenshots.py 和 "
              "generate_chat_screenshots.py 完成后再运行全量标注。")
        ans = input("是否继续？(y/n): ").strip().lower()
        if ans != "y":
            print("已取消。")
            sys.exit(0)

    # 构建命令
    cmd = [
        sys.executable, "-m", PIPELINE_MODULE,
        "--data-dir", "knowledge_graph/processed_data",
        "--output-dir", "knowledge_graph/processed_data",
        "--cache-dir", "knowledge_graph/annotation_cache",
        "--version", "v2.0.0",
        "--cache-scope", "default",
        "--mode", args.mode,
        "--sample-size", str(args.sample_size),
        "--workers", str(args.workers),
    ]

    if args.use_local_model:
        cmd.append("--use-local-model")
        if args.local_model_path:
            cmd += ["--local-model-path", args.local_model_path]
        cmd.append("--use-api")  # use_api=True 触发实际标注（本地模型优先）
    elif args.use_api:
        cmd.append("--use-api")

    print(f"\n运行命令: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
