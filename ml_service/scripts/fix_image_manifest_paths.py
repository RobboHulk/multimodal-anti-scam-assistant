"""
fix_image_manifest_paths.py
============================
将 images_manifest.json 中的 macOS 绝对路径批量修复为项目内相对路径。

macOS 原始路径格式：
  /Users/hulk.q/Desktop/multimodal anti_fraud agent/datasets/generated_screenshots/<filename>

修复后相对路径格式（相对于项目根目录）：
  datasets/generated_screenshots/<filename>

同时更新 screenshots_manifest.json 中的 source_html 路径：
  datasets/archive/malicious web pages/<name>.htm
  → datasets/maliciousWebPages/<name>.htm
"""
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGES_MANIFEST = PROJECT_ROOT / "knowledge_graph" / "processed_data" / "images_manifest.json"
SCREENSHOTS_MANIFEST = PROJECT_ROOT / "knowledge_graph" / "processed_data" / "screenshots_manifest.json"


def fix_images_manifest():
    print(f"读取 {IMAGES_MANIFEST.name}...")
    with open(IMAGES_MANIFEST, encoding="utf-8") as f:
        items = json.load(f)

    # macOS 路径前缀（可能有空格变体）
    MAC_PREFIXES = [
        "/Users/hulk.q/Desktop/multimodal anti_fraud agent/",
        "/Users/hulk.q/Desktop/multimodal_anti_fraud_agent/",
        "/Users/hulk.q/LLM/multimodal_antifraud_agent/",
    ]

    fixed = skipped = 0
    for item in items:
        fp = item.get("file_path", "")
        if not fp:
            continue
        replaced = False
        for prefix in MAC_PREFIXES:
            if fp.startswith(prefix):
                rel = fp[len(prefix):]  # 去掉 macOS 前缀，保留 datasets/... 部分
                item["file_path"] = rel
                replaced = True
                fixed += 1
                break
        if not replaced and fp.startswith("/"):
            # 其他 macOS 绝对路径：尝试提取 datasets/ 之后的部分
            idx = fp.find("datasets/")
            if idx != -1:
                item["file_path"] = fp[idx:]
                fixed += 1
            else:
                skipped += 1

    # 备份原文件
    backup = IMAGES_MANIFEST.with_suffix(".json.bak")
    shutil.copy2(IMAGES_MANIFEST, backup)
    print(f"  已备份到 {backup.name}")

    with open(IMAGES_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"  images_manifest: 修复 {fixed} 条，跳过 {skipped} 条")

    # 验证：检查修复后路径是否存在
    exist = sum(1 for x in items if (PROJECT_ROOT / x.get("file_path", "")).exists())
    print(f"  修复后实际存在的图片文件: {exist}/{len(items)}")
    return fixed


def fix_screenshots_manifest():
    print(f"\n读取 {SCREENSHOTS_MANIFEST.name}...")
    with open(SCREENSHOTS_MANIFEST, encoding="utf-8") as f:
        data = json.load(f)

    is_dict = isinstance(data, dict)
    items = list(data.values()) if is_dict else data

    fixed = 0
    for item in items:
        src = item.get("source_html", "")
        # 旧路径：datasets/archive/malicious web pages/<name>.htm
        # 新路径：datasets/maliciousWebPages/<name>.htm
        if "datasets/archive/malicious web pages/" in src:
            filename = Path(src).name
            item["source_html"] = f"datasets/maliciousWebPages/{filename}"
            fixed += 1
        elif src.startswith("/Users/"):
            # macOS 绝对路径
            filename = Path(src).name
            item["source_html"] = f"datasets/maliciousWebPages/{filename}"
            fixed += 1

    backup = SCREENSHOTS_MANIFEST.with_suffix(".json.bak")
    shutil.copy2(SCREENSHOTS_MANIFEST, backup)

    with open(SCREENSHOTS_MANIFEST, "w", encoding="utf-8") as f:
        if is_dict:
            # 重建 dict（key 不变）
            keys = list(data.keys())
            new_data = {k: v for k, v in zip(keys, items)}
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # 验证：检查 source_html 是否存在
    exist = sum(1 for x in items if (PROJECT_ROOT / x.get("source_html", "")).exists())
    print(f"  screenshots_manifest: 修复 {fixed} 条")
    print(f"  修复后 source_html 实际存在: {exist}/{len(items)}")
    return fixed


if __name__ == "__main__":
    fix_images_manifest()
    fix_screenshots_manifest()
    print("\n路径修复完成。")
