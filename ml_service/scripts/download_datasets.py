"""
download_datasets.py
====================
下载意图识别训练调优所需的两个外部数据集：
- quanshiyun/anti_fraud_dataset (HuggingFace)
- JimmyMa99/TeleAntiFraud-28k (ModelScope)

说明：
- 脚本优先尝试使用 huggingface-cli / modelscope 命令行
- 若命令不存在，则打印手动下载命令
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "datasets" / "external"

HF_DATASET = "quanshiyun/anti_fraud_dataset"
MS_DATASET = "JimmyMa99/TeleAntiFraud-28k"


def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    try:
        print(f"运行命令: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)
        return True
    except FileNotFoundError:
        print(f"命令不存在: {cmd[0]}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"命令失败: {e}")
        return False


def download_hf(output_dir: Path) -> bool:
    hf_cli = shutil.which("huggingface-cli")
    if not hf_cli:
        print("未找到 huggingface-cli，请手动执行：")
        print(f"  huggingface-cli download {HF_DATASET} --repo-type dataset --local-dir {output_dir / 'anti_fraud_dataset'}")
        return False
    return run_command([
        hf_cli,
        "download",
        HF_DATASET,
        "--repo-type",
        "dataset",
        "--local-dir",
        str(output_dir / "anti_fraud_dataset"),
    ])


def download_ms(output_dir: Path) -> bool:
    ms_cli = shutil.which("modelscope")
    if not ms_cli:
        print("未找到 modelscope，请手动执行：")
        print(f"  modelscope download --dataset {MS_DATASET} --local_dir {output_dir / 'TeleAntiFraud-28k'}")
        return False
    return run_command([
        ms_cli,
        "download",
        "--dataset",
        MS_DATASET,
        "--local_dir",
        str(output_dir / "TeleAntiFraud-28k"),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="下载意图识别训练调优所需外部数据集")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== 下载 HuggingFace 数据集 ===")
    hf_ok = download_hf(output_dir)

    print("\n=== 下载 ModelScope 数据集 ===")
    ms_ok = download_ms(output_dir)

    print("\n=== 完成 ===")
    print(f"HuggingFace: {'成功' if hf_ok else '请手动下载'}")
    print(f"ModelScope: {'成功' if ms_ok else '请手动下载'}")


if __name__ == "__main__":
    main()
