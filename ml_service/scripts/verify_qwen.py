"""快速验证 Qwen2.5-Omni-7B snapshot 文件完整性（不加载权重，只检查配置）"""
import json
from pathlib import Path

SNAPSHOT = Path(r"D:\Desktop\models\Qwen2.5-Omni-7B\snapshots\ae9e1690543ffd5c0221dc27f79834d0294cba00")

required = [
    "config.json", "generation_config.json", "tokenizer.json",
    "tokenizer_config.json", "vocab.json", "merges.txt",
    "model.safetensors.index.json", "preprocessor_config.json",
    "model-00001-of-00005.safetensors", "model-00002-of-00005.safetensors",
    "model-00003-of-00005.safetensors", "model-00004-of-00005.safetensors",
    "model-00005-of-00005.safetensors", "spk_dict.pt",
]

print("=== 文件完整性检查 ===")
all_ok = True
for name in required:
    f = SNAPSHOT / name
    sz = f.stat().st_size if f.exists() else -1
    status = "OK" if sz > 0 else ("MISSING" if sz == -1 else "EMPTY")
    if status != "OK":
        all_ok = False
    print(f"  [{status:7}] {name}  ({sz/1024/1024:.2f} MB)" if sz > 0 else f"  [{status:7}] {name}")

print()
# 验证 config.json 可解析
try:
    cfg = json.loads((SNAPSHOT / "config.json").read_text(encoding="utf-8"))
    print(f"config.json: model_type={cfg.get('model_type')}, architectures={cfg.get('architectures')}")
except Exception as e:
    print(f"config.json 解析失败: {e}")
    all_ok = False

# 验证 model.safetensors.index.json
try:
    idx = json.loads((SNAPSHOT / "model.safetensors.index.json").read_text(encoding="utf-8"))
    total_params = len(idx.get("weight_map", {}))
    print(f"model.safetensors.index.json: {total_params} 个参数张量")
except Exception as e:
    print(f"index.json 解析失败: {e}")
    all_ok = False

print()
print("结论:", "所有文件完整，可以加载模型" if all_ok else "存在问题，请检查上方 EMPTY/MISSING 项")
