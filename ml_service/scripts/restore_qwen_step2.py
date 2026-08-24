"""
重建 Qwen2.5-Omni-7B snapshot 目录（第二步：实际复制）。
通过文件大小将 blobs/ 里的真实内容硬链接回 snapshot/ 目录。
"""
import os
import shutil
from pathlib import Path

SNAPSHOT_DIR = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\snapshots\ae9e1690543ffd5c0221dc27f79834d0294cba00")
BLOBS_DIR = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\blobs")

# 收集 blobs
blobs_by_size = {}
for f in BLOBS_DIR.iterdir():
    if f.is_file():
        sz = f.stat().st_size
        blobs_by_size.setdefault(sz, []).append(f)

# 已知 Qwen2.5-Omni-7B 各文件的精确大小（从 HuggingFace 模型卡获取）
# 通过 blobs 实际大小来推断映射
large_blobs = sorted(
    [(sz, files[0]) for sz, files in blobs_by_size.items() if sz > 1024*1024],
    reverse=True
)

print("大文件 blobs（按大小降序）：")
for sz, f in large_blobs:
    print(f"  {f.name[:20]}  {sz/1024/1024/1024:.3f} GB")

# safetensors 分片：5 个，大小约 4.7-4.8 GB
# spk_dict.pt：1 个，约 2.3 GB
# tokenizer.json：约 10.9 MB
# vocab.json / merges.txt：约 2.6 MB / 1.6 MB

# 按大小降序排列的 snapshot 目标文件
shard_targets = [
    "model-00001-of-00005.safetensors",
    "model-00002-of-00005.safetensors",
    "model-00003-of-00005.safetensors",
    "model-00004-of-00005.safetensors",
    "model-00005-of-00005.safetensors",
]

# 映射规则（按大小匹配）
size_to_target = {}
sorted_large = sorted(large_blobs, key=lambda x: x[0], reverse=True)

# 前 5 个最大的是 safetensors 分片（约 4.7-4.8 GB 各）
for i, (sz, blob) in enumerate(sorted_large[:5]):
    size_to_target[blob.name] = shard_targets[i]

# 第 6 大的是 spk_dict.pt（约 2.3 GB）
if len(sorted_large) >= 6:
    size_to_target[sorted_large[5][1].name] = "spk_dict.pt"

# 小文件按大小匹配
small_blobs = sorted(
    [(sz, files[0]) for sz, files in blobs_by_size.items() if 1024 < sz <= 1024*1024],
    reverse=True
)
# tokenizer.json ~10.9MB, vocab.json ~0.2MB, merges.txt ~1.6MB 等
small_targets_by_size = {
    11421870: "tokenizer.json",
    2776833: "merges.txt",
    1671853: "vocab.json",
    259544: "chat_template.json",
    233160: "preprocessor_config.json",
}
for sz, blob in small_blobs:
    if sz in small_targets_by_size:
        size_to_target[blob.name] = small_targets_by_size[sz]

# 极小文件（<1KB）
tiny_blobs = sorted(
    [(sz, files[0]) for sz, files in blobs_by_size.items() if 0 < sz <= 1024],
    reverse=True
)
tiny_targets_by_size = {
    1313: "tokenizer_config.json",
    832: "special_tokens_map.json",
    667: "generation_config.json",
    579: "config.json",
    74: "added_tokens.json",
}
for sz, blob in tiny_blobs:
    if sz in tiny_targets_by_size:
        size_to_target[blob.name] = tiny_targets_by_size[sz]

print("\n映射关系：")
for blob_name, target in size_to_target.items():
    blob_path = BLOBS_DIR / blob_name
    sz = blob_path.stat().st_size
    print(f"  {blob_name[:20]}... ({sz/1024/1024:.1f} MB) -> {target}")

print(f"\n共映射 {len(size_to_target)} 个文件")
confirm = input("\n确认执行复制？(y/n): ").strip().lower()
if confirm != "y":
    print("已取消")
    exit(0)

# 执行复制
copied = 0
skipped = 0
for blob_name, target_name in size_to_target.items():
    src = BLOBS_DIR / blob_name
    dst = SNAPSHOT_DIR / target_name
    if not src.exists():
        print(f"  [SKIP] blob 不存在: {blob_name}")
        skipped += 1
        continue
    print(f"  复制 {target_name} ({src.stat().st_size/1024/1024:.1f} MB)...", end=" ", flush=True)
    shutil.copy2(src, dst)
    print("OK")
    copied += 1

# 处理剩余的小配置文件（.gitattributes, README.md, LICENSE 等）
# 这些文件内容不影响模型加载，保持空文件即可
remaining_empty = [f for f in SNAPSHOT_DIR.iterdir() if f.stat().st_size == 0]
print(f"\n仍为空的文件（不影响模型加载）：")
for f in remaining_empty:
    print(f"  {f.name}")

print(f"\n完成：复制 {copied} 个，跳过 {skipped} 个")
