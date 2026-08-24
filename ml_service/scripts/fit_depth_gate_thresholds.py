"""
fit_depth_gate_thresholds.py
===========================
从标注数据拟合 DepthGate 的 none_threshold 和 deep_threshold。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intent_recognizer.cue_extractor import MultiModalCueExtractor
from intent_recognizer.depth_gate import DepthGate
from intent_recognizer.schema import IntentInput


def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def update_config(path: Path, none_threshold: float, deep_threshold: float) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"DEFAULT_NONE_THRESHOLD = [0-9.]+", f"DEFAULT_NONE_THRESHOLD = {none_threshold:.6f}", text, count=1)
    text = re.sub(r"DEFAULT_DEEP_THRESHOLD = [0-9.]+", f"DEFAULT_DEEP_THRESHOLD = {deep_threshold:.6f}", text, count=1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="拟合 DepthGate 阈值")
    parser.add_argument("--input", default=str(PROJECT_ROOT / "intent_recognizer" / "data" / "auto_labeled.jsonl"))
    parser.add_argument("--config", default=str(PROJECT_ROOT / "intent_recognizer" / "config.py"))
    args = parser.parse_args()

    items = load_jsonl(Path(args.input))
    extractor = MultiModalCueExtractor()
    gate = DepthGate()

    scores = []
    none_labels = []
    deep_labels = []
    for item in items:
        intent_input = IntentInput(
            query=item.get("query", ""),
            image_ocr_text=item.get("image_ocr_text", ""),
            image_caption=item.get("image_caption", ""),
            audio_text=item.get("audio_text", ""),
            audio_deepfake_score=item.get("audio_deepfake_score"),
        )
        cues = extractor.extract(intent_input)
        score, _ = gate.score(intent_input, cues)
        scores.append(score)
        none_labels.append(item.get("risk_stage", "S0") == "S0")
        deep_labels.append(item.get("risk_stage", "S0") in {"S3", "S4", "S5", "S6"})

    result = gate.fit_thresholds(scores, none_labels, deep_labels)
    update_config(Path(args.config), result["none_threshold"], result["deep_threshold"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
