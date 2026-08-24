"""通过内容特征精确重映射 Qwen2.5-Omni-7B 的 blob 文件到正确的 snapshot 文件名"""
import shutil
from pathlib import Path

SNAP = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\snapshots\ae9e1690543ffd5c0221dc27f79834d0294cba00")
BLOBS = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\blobs")


def identify(path: Path) -> str | None:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")[:300]
    except Exception:
        return None
    if '"architectures"' in content and "Qwen2_5OmniModel" in content:
        return "config.json"
    if '"_from_model_config"' in content and "transformers_version" in content:
        return "generation_config.json"
    if '"added_tokens_decoder"' in content:
        return "tokenizer_config.json"
    if "tool_call" in content and "endoftext" in content:
        return "added_tokens.json"
    if "chunk_length" in content and "WhisperFeatureExtractor" in content:
        return "preprocessor_config.json"
    if "additional_special_tokens" in content and "im_start" in content:
        return "special_tokens_map.json"
    if "filter=lfs" in content and "diff=lfs" in content:
        return ".gitattributes"
    if "Apache License" in content and "Version 2.0" in content:
        return "LICENSE"
    if content.strip().startswith("---") and "license" in content and "huggingface" in content:
        return "README.md"
    return None


print("=== 识别 blob 内容 ===")
blob_identity: dict[str, Path] = {}
for f in BLOBS.iterdir():
    if f.is_file() and f.stat().st_size < 100_000:
        identity = identify(f)
        if identity:
            blob_identity[identity] = f
            print(f"  {identity:35} <- {f.name[:20]}... ({f.stat().st_size} bytes)")

print(f"\n共识别 {len(blob_identity)} 个文件，开始复制...")
for target_name, src in blob_identity.items():
    dst = SNAP / target_name
    shutil.copy2(src, dst)
    print(f"  OK: {target_name}")

# 最终验证
print("\n=== 最终验证 ===")
import json
for name in ["config.json", "generation_config.json", "tokenizer_config.json", "added_tokens.json"]:
    f = SNAP / name
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        keys = list(data.keys())[:3]
        print(f"  {name}: OK, keys={keys}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")
