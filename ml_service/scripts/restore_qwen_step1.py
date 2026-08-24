"""
重建 Qwen2.5-Omni-7B snapshot 目录。
macOS 上的 HuggingFace 缓存使用符号链接，迁移到 Windows 后链接变成了 0 字节空文件。
本脚本通过文件大小匹配，将 blobs/ 里的真实内容硬链接（或复制）回 snapshot/ 目录。
"""
import os
import shutil
from pathlib import Path

SNAPSHOT_DIR = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\snapshots\ae9e1690543ffd5c0221dc27f79834d0294cba00")
BLOBS_DIR = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\blobs")

# 已知文件名 -> blob 哈希的映射（根据文件大小和已知模型结构推断）
# 先收集 blobs 里所有文件的大小
blobs = {f.name: f for f in BLOBS_DIR.iterdir() if f.is_file()}
blob_sizes = {f.stat().st_size: f for f in blobs.values()}

print("=== Blobs 文件列表 ===")
for name, f in sorted(blobs.items(), key=lambda x: x[1].stat().st_size, reverse=True):
    size_mb = f.stat().st_size / 1024 / 1024
    print(f"  {name[:16]}...  {size_mb:.1f} MB")

print("\n=== Snapshot 文件（当前为空）===")
snapshot_files = list(SNAPSHOT_DIR.iterdir())
for f in snapshot_files:
    print(f"  {f.name}  ({f.stat().st_size} bytes)")

# 对于非零大小的 blob，尝试按大小匹配到 snapshot 文件
# safetensors 分片大小是固定的，可以精确匹配
large_blobs = sorted(
    [(f.stat().st_size, f) for f in blobs.values() if f.stat().st_size > 1024*1024],
    reverse=True
)

print(f"\n共 {len(large_blobs)} 个大文件 blob，{len(snapshot_files)} 个 snapshot 文件")
print("\n需要手动确认映射关系后再执行复制。")
print("请运行 restore_qwen_step2.py 执行实际复制。")
