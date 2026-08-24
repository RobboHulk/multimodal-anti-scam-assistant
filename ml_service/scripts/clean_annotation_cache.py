"""
clean_annotation_cache.py
==========================
清理 annotation_cache/image_annotations_v1.0.0.jsonl 中的无效记录：
  - error 字段非空
  - ocr_text / image_caption 包含 "[Mock]"
  - ocr_text 和 image_caption 均为空（未真实标注）

保留真实标注记录，输出到 image_annotations_v2.0.0.jsonl（作为 v2.0.0 的初始缓存）。
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "knowledge_graph" / "annotation_cache"
SRC = CACHE_DIR / "image_annotations_v1.0.0.jsonl"
DST = CACHE_DIR / "image_annotations_v2.0.0.jsonl"


def is_real_annotation(record: dict) -> bool:
    """判断是否为真实的 Qwen-VL 标注结果（非 Mock、非错误）。"""
    if record.get("error"):
        return False
    ocr = str(record.get("ocr_text") or "")
    caption = str(record.get("image_caption") or "")
    if "[Mock]" in ocr or "[Mock]" in caption:
        return False
    # 必须有实质内容
    if not ocr.strip() and not caption.strip():
        return False
    return True


def main():
    print(f"读取缓存: {SRC.name}")
    lines = SRC.read_text(encoding="utf-8").splitlines()
    total = real = mock = err = empty = 0

    kept = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            err += 1
            continue

        if record.get("error"):
            err += 1
        elif "[Mock]" in str(record.get("ocr_text", "")) or "[Mock]" in str(record.get("image_caption", "")):
            mock += 1
        elif not str(record.get("ocr_text", "")).strip() and not str(record.get("image_caption", "")).strip():
            empty += 1
        else:
            real += 1
            kept.append(record)

    print(f"  总计: {total} 条")
    print(f"  真实标注: {real} 条 → 保留")
    print(f"  Mock: {mock} 条 → 丢弃")
    print(f"  错误: {err} 条 → 丢弃")
    print(f"  空内容: {empty} 条 → 丢弃")

    # 写出干净的 v2.0.0 缓存
    with open(DST, "w", encoding="utf-8") as f:
        for record in kept:
            # 更新版本号
            record["annotation_version"] = "v2.0.0"
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n输出: {DST.name}（{len(kept)} 条真实标注）")
    print("v2.0.0 缓存已就绪，重新运行标注管道时将从这 {len(kept)} 条开始断点续传。")


if __name__ == "__main__":
    main()
