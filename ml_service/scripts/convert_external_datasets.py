"""
convert_external_datasets.py
============================
将外部反诈数据集转换为 IntentEvalRecord 兼容格式。
输出到 intent_recognizer/data/external_converted.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = PROJECT_ROOT / "datasets" / "external"
OUTPUT_PATH = PROJECT_ROOT / "intent_recognizer" / "data" / "external_converted.jsonl"

TELE_TYPE_MAP = {
    "Investment Fraud": "INVESTMENT_FRAUD",
    "Phishing": "PHISHING_LINK_QRCODE",
    "Identity Theft": "IMPERSONATE_POLICE_GOV",
    "Lottery Fraud": "LOTTERY_FRAUD",
    "Banking Fraud": "IMPERSONATE_ECOM_CUSTOMER_SERVICE",
    "Kidnapping Fraud": "EMERGENCY_IMPERSONATION",
    "Customer Service Fraud": "IMPERSONATE_ECOM_CUSTOMER_SERVICE",
}

FILE_TYPE_MAP = {
    "投资诈骗": "INVESTMENT_FRAUD",
    "网络贷款诈骗": "LOAN_SCAM",
    "兼职刷单诈骗": "PART_TIME_JOB_FRAUD",
    "冒充客服诈骗": "IMPERSONATE_ECOM_CUSTOMER_SERVICE",
    "短信诈骗": "PHISHING_LINK_QRCODE",
    "虚假购物诈骗": "SHOPPING_FRAUD",
    "虚拟货币诈骗": "INVESTMENT_FRAUD",
    "二手交易诈骗": "SHOPPING_FRAUD",
    "杀猪盘": "ROMANCE_FRAUD",
    "微商代理诈骗": "SHOPPING_FRAUD",
    "传销诈骗": "OTHER_UNKNOWN",
    "网络赌博诈骗": "GAMBLING_FRAUD",
}


def convert_hf_dataset(root: Path) -> List[Dict]:
    records: List[Dict] = []
    if not root.exists():
        return records

    for path in sorted(root.glob("*.jsonl")):
        # 从文件名中猜类别（若可用）
        coarse_category = "OTHER_UNKNOWN"
        for zh_name, mapped in FILE_TYPE_MAP.items():
            if zh_name in path.name:
                coarse_category = mapped
                break

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                query = item.get("input", "")
                output_text = item.get("output", "{}")
                try:
                    output = json.loads(output_text)
                except Exception:
                    output = {}
                records.append(
                    {
                        "query": query,
                        "is_fraud_relevant": bool(output.get("is_fraud", False)),
                        "coarse_category": coarse_category,
                        "risk_stage": "S1",  # 占位，后续 auto_label_risk_stage.py 自动标注
                        "recommended_action": "verify",
                        "source_dataset": "quanshiyun/anti_fraud_dataset",
                    }
                )
    return records


def convert_tele_dataset(root: Path) -> List[Dict]:
    records: List[Dict] = []
    if not root.exists():
        return records

    # 递归找 json/jsonl/csv 文件
    for path in list(root.rglob("*.json")) + list(root.rglob("*.jsonl")) + list(root.rglob("*.csv")):
        if path.suffix == ".csv":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    query = row.get("text") or row.get("query") or row.get("transcript") or ""
                    fraud_type = row.get("fraud_type") or row.get("label") or ""
                    mapped_type = TELE_TYPE_MAP.get(fraud_type, "OTHER_UNKNOWN")
                    records.append(
                        {
                            "query": query,
                            "is_fraud_relevant": mapped_type != "OTHER_UNKNOWN",
                            "coarse_category": mapped_type,
                            "risk_stage": "S1",
                            "recommended_action": "verify",
                            "source_dataset": "TeleAntiFraud-28k",
                        }
                    )
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue
                    query = item.get("text") or item.get("query") or item.get("transcript") or item.get("input") or ""
                    fraud_type = item.get("fraud_type") or item.get("label") or ""
                    mapped_type = TELE_TYPE_MAP.get(fraud_type, "OTHER_UNKNOWN")
                    records.append(
                        {
                            "query": query,
                            "is_fraud_relevant": mapped_type != "OTHER_UNKNOWN",
                            "coarse_category": mapped_type,
                            "risk_stage": "S1",
                            "recommended_action": "verify",
                            "source_dataset": "TeleAntiFraud-28k",
                        }
                    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="转换外部数据集为 IntentEvalRecord 兼容格式")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    hf_root = EXTERNAL_DIR / "anti_fraud_dataset"
    tele_root = EXTERNAL_DIR / "TeleAntiFraud-28k"

    records = []
    records.extend(convert_hf_dataset(hf_root))
    records.extend(convert_tele_dataset(tele_root))

    # 去空 query
    records = [r for r in records if r.get("query", "").strip()]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"转换完成: {len(records)} 条 -> {output_path}")


if __name__ == "__main__":
    main()
