"""
fit_confidence_weights.py
=========================
用标注数据拟合 5 个置信度融合权重，以及 rule-model agreement 的 3 个参数。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intent_recognizer.analyzer import IntentAnalyzer
from intent_recognizer.config import (
    RULE_MODEL_AGREEMENT_BASE,
    RULE_MODEL_AGREEMENT_STAGE_BONUS,
    RULE_MODEL_AGREEMENT_TYPE_BONUS,
)
from intent_recognizer.confidence import ConfidenceSignals
from intent_recognizer.cue_extractor import MultiModalCueExtractor
from intent_recognizer.schema import IntentInput
from intent_recognizer.safety_rules import heuristic_risk_stage

try:
    from sklearn.linear_model import LogisticRegression
except Exception:  # pragma: no cover
    LogisticRegression = None

SIGNAL_NAMES = [
    "model_confidence",
    "self_consistency",
    "rule_model_agreement",
    "cue_density_prior",
    "cross_modal_support",
]


def load_jsonl(path: Path) -> List[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def infer_signals(item: dict, analyzer: IntentAnalyzer, extractor: MultiModalCueExtractor) -> ConfidenceSignals:
    intent_input = IntentInput(
        query=item.get("query", ""),
        image_ocr_text=item.get("image_ocr_text", ""),
        image_caption=item.get("image_caption", ""),
        audio_text=item.get("audio_text", ""),
        audio_deepfake_score=item.get("audio_deepfake_score"),
    )
    cues = extractor.extract(intent_input)
    predicted_category = item.get("coarse_category", cues.inferred_scam_type)
    predicted_stage = item.get("risk_stage", "S0")
    heuristic_stage = heuristic_risk_stage(intent_input, cues)
    raw_confidence = float(item.get("risk_stage_confidence", item.get("confidence", 0.75 if item.get("is_fraud_relevant") else 0.25)))
    self_consistency = float(item.get("self_consistency", 0.75))
    return ConfidenceSignals(
        model_confidence=raw_confidence,
        self_consistency=self_consistency,
        rule_model_agreement=analyzer._estimate_rule_model_agreement(
            category=predicted_category,
            stage=predicted_stage,
            heuristic_stage=heuristic_stage,
            inferred_type=cues.inferred_scam_type,
        ),
        cue_density_prior=min(cues.cue_density_score / 5.0, 1.0),
        cross_modal_support=1.0 if cues.cross_modal_matches else 0.0,
    )


def update_config(path: Path, weights: dict, params: dict) -> None:
    text = path.read_text(encoding="utf-8")
    weights_block = "CONFIDENCE_WEIGHTS: Dict[str, float] = {\n" + "\n".join(
        f'    "{k}": {v:.6f},' for k, v in weights.items()
    ) + "\n}"
    text = re.sub(r"CONFIDENCE_WEIGHTS: Dict\[str, float\] = \{[\s\S]*?\n\}", weights_block, text, count=1)
    text = re.sub(r"RULE_MODEL_AGREEMENT_BASE = [0-9.]+", f"RULE_MODEL_AGREEMENT_BASE = {params['base']:.6f}", text, count=1)
    text = re.sub(r"RULE_MODEL_AGREEMENT_TYPE_BONUS = [0-9.]+", f"RULE_MODEL_AGREEMENT_TYPE_BONUS = {params['type_bonus']:.6f}", text, count=1)
    text = re.sub(r"RULE_MODEL_AGREEMENT_STAGE_BONUS = [0-9.]+", f"RULE_MODEL_AGREEMENT_STAGE_BONUS = {params['stage_bonus']:.6f}", text, count=1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="拟合置信度融合权重")
    parser.add_argument("--input", default=str(PROJECT_ROOT / "intent_recognizer" / "data" / "auto_labeled.jsonl"))
    parser.add_argument("--config", default=str(PROJECT_ROOT / "intent_recognizer" / "config.py"))
    args = parser.parse_args()

    items = load_jsonl(Path(args.input))
    analyzer = IntentAnalyzer(enable_llm=False)
    extractor = MultiModalCueExtractor()

    X = []
    y = []
    match_type = []
    match_stage = []
    for item in items:
        sig = infer_signals(item, analyzer, extractor)
        X.append([
            sig.model_confidence,
            sig.self_consistency,
            sig.rule_model_agreement,
            sig.cue_density_prior,
            sig.cross_modal_support,
        ])
        y.append(int(bool(item.get("is_fraud_relevant", False))))
        inferred_type = extractor.extract(IntentInput(text=item.get("query", ""))).inferred_scam_type
        match_type.append(int(item.get("coarse_category", "OTHER_UNKNOWN") == inferred_type))
        match_stage.append(int(item.get("risk_stage", "S0") in {"S3", "S4", "S5", "S6"}))

    if not X:
        raise RuntimeError("输入数据为空")

    if LogisticRegression is not None:
        lr = LogisticRegression(fit_intercept=False, C=1.0, max_iter=1000)
        lr.fit(X, y)
        raw = [abs(v) for v in lr.coef_[0].tolist()]
    else:
        raw = [sum(col) / len(col) for col in zip(*X)]

    s = sum(raw) or 1.0
    weights = {name: value / s for name, value in zip(SIGNAL_NAMES, raw)}

    total = len(y) or 1
    params = {
        "base": RULE_MODEL_AGREEMENT_BASE,
        "type_bonus": sum(match_type) / total * 0.5,
        "stage_bonus": sum(match_stage) / total * 0.3,
    }

    update_config(Path(args.config), weights, params)
    print(json.dumps({"weights": weights, "rule_model_agreement": params}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
