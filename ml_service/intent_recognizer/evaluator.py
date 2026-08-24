"""意图识别评测框架。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from intent_recognizer.analyzer import IntentAnalyzer
from intent_recognizer.schema import IntentInput

try:
    import dspy

    class IntentAnalysisSignature(dspy.Signature):
        """分析用户输入的诈骗风险意图。"""

        query = dspy.InputField(desc="用户原始输入")
        cues = dspy.InputField(desc="结构化多模态线索")
        memory = dspy.InputField(desc="对话历史摘要")
        is_fraud_relevant = dspy.OutputField(desc="是否诈骗相关")
        coarse_category = dspy.OutputField(desc="诈骗主类")
        risk_stage = dspy.OutputField(desc="风险阶段 S0-S6")
        recommended_action = dspy.OutputField(desc="建议动作")
        confidence = dspy.OutputField(desc="模型置信度 0-1")
        reasoning = dspy.OutputField(desc="简要推理依据")

except ImportError:  # pragma: no cover
    IntentAnalysisSignature = None


@dataclass
class IntentEvalRecord:
    query: str
    is_fraud_relevant: bool
    coarse_category: str
    risk_stage: str
    recommended_action: str
    image_ocr_text: str = ""
    image_caption: str = ""
    audio_text: str = ""
    audio_deepfake_score: float | None = None


class IntentEvaluator:
    """面向 Prompt 与规则迭代的轻量评测器。"""

    def __init__(self, analyzer: IntentAnalyzer) -> None:
        self.analyzer = analyzer

    def evaluate_records(self, records: Iterable[IntentEvalRecord]) -> Dict[str, Any]:
        records = list(records)
        if not records:
            return {"total": 0}

        fraud_correct = 0
        category_correct = 0
        stage_correct = 0
        action_correct = 0
        details: List[Dict[str, Any]] = []
        brier = 0.0

        for idx, record in enumerate(records):
            result = self.analyzer.analyze(
                IntentInput(
                    query=record.query,
                    session_id=f"eval-{idx}",
                    image_ocr_text=record.image_ocr_text,
                    image_caption=record.image_caption,
                    audio_text=record.audio_text,
                    audio_deepfake_score=record.audio_deepfake_score,
                )
            )
            fraud_correct += int(result.is_fraud_relevant == record.is_fraud_relevant)
            category_correct += int(result.coarse_category == record.coarse_category)
            stage_correct += int(result.risk_stage == record.risk_stage)
            action_correct += int(result.recommended_action == record.recommended_action)
            brier += (float(result.confidence) - (1.0 if record.is_fraud_relevant else 0.0)) ** 2
            details.append(
                {
                    "query": record.query,
                    "expected": {
                        "is_fraud_relevant": record.is_fraud_relevant,
                        "coarse_category": record.coarse_category,
                        "risk_stage": record.risk_stage,
                        "recommended_action": record.recommended_action,
                    },
                    "predicted": result.to_dict(),
                }
            )

        total = len(records)
        return {
            "total": total,
            "fraud_relevance_accuracy": round(fraud_correct / total, 4),
            "category_accuracy": round(category_correct / total, 4),
            "risk_stage_accuracy": round(stage_correct / total, 4),
            "action_accuracy": round(action_correct / total, 4),
            "brier_score": round(brier / total, 4),
            "details": details,
        }

    @staticmethod
    def load_jsonl(path: str) -> List[IntentEvalRecord]:
        records: List[IntentEvalRecord] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(IntentEvalRecord(**payload))
        return records

    @staticmethod
    def to_dspy_examples(records: Iterable[IntentEvalRecord]) -> List[Dict[str, Any]]:
        """导出为 DSPy 可消费的样例结构。"""
        examples: List[Dict[str, Any]] = []
        for record in records:
            examples.append(
                {
                    "input": {
                        "query": record.query,
                        "cues": {
                            "image_ocr_text": record.image_ocr_text,
                            "image_caption": record.image_caption,
                            "audio_text": record.audio_text,
                            "audio_deepfake_score": record.audio_deepfake_score,
                        },
                        "memory": "",
                    },
                    "output": {
                        "is_fraud_relevant": record.is_fraud_relevant,
                        "coarse_category": record.coarse_category,
                        "risk_stage": record.risk_stage,
                        "recommended_action": record.recommended_action,
                    },
                }
            )
        return examples

    @staticmethod
    def generate_eval_matrix() -> List[IntentEvalRecord]:
        """生成 7 风险阶段 × 16 诈骗类型的最小覆盖评测集（每格至少 1 条）。"""
        # fmt: off
        _MATRIX: List[Dict[str, Any]] = [
            # S0 — 无风险 / 闲聊
            {"query": "今天天气怎么样？", "is_fraud_relevant": False, "coarse_category": "OTHER_UNKNOWN", "risk_stage": "S0", "recommended_action": "none"},
            {"query": "帮我查一下附近的餐厅", "is_fraud_relevant": False, "coarse_category": "OTHER_UNKNOWN", "risk_stage": "S0", "recommended_action": "none"},
            # S1 — 初步接触 / 信息收集
            {"query": "有人加我微信说可以帮我理财，收益很高", "is_fraud_relevant": True, "coarse_category": "INVESTMENT_FRAUD", "risk_stage": "S1", "recommended_action": "educate"},
            {"query": "网上认识了一个人，说自己是军人，一直找我聊天", "is_fraud_relevant": True, "coarse_category": "ROMANCE_FRAUD", "risk_stage": "S1", "recommended_action": "educate"},
            {"query": "有个兼职说每天刷单可以赚几百块", "is_fraud_relevant": True, "coarse_category": "PART_TIME_JOB_FRAUD", "risk_stage": "S1", "recommended_action": "educate"},
            {"query": "收到短信说我中奖了，需要先交税", "is_fraud_relevant": True, "coarse_category": "LOTTERY_FRAUD", "risk_stage": "S1", "recommended_action": "educate"},
            # S2 — 建立信任 / 诱导深入
            {"query": "对方让我下载一个APP，说是专业投资平台", "is_fraud_relevant": True, "coarse_category": "INVESTMENT_FRAUD", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "刷单平台让我先垫付200元，说完成任务后返还", "is_fraud_relevant": True, "coarse_category": "PART_TIME_JOB_FRAUD", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "有人说帮我办理低息贷款，让我提供身份证和银行卡", "is_fraud_relevant": True, "coarse_category": "LOAN_SCAM", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "对方说是公安局的，让我配合调查，不要告诉家人", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S2", "recommended_action": "warn"},
            # S3 — 施压 / 诱导操作
            {"query": "平台说我的账户异常，需要转账到指定账户解冻", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "对方让我把钱转到安全账户配合调查", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "贷款平台说放款前需要先交5000元保证金", "is_fraud_relevant": True, "coarse_category": "LOAN_SCAM", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "网恋对象说急需钱治病，让我买礼品卡发给他", "is_fraud_relevant": True, "coarse_category": "ROMANCE_FRAUD", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "有人让我共享屏幕帮我操作银行APP", "is_fraud_relevant": True, "coarse_category": "TECH_SUPPORT_FRAUD", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "对方说我的快递涉及走私，让我配合转账", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S3", "recommended_action": "block"},
            # S4 — 资金操作 / 高危
            {"query": "我已经转了3万，平台说还需要再转5万才能提现", "is_fraud_relevant": True, "coarse_category": "INVESTMENT_FRAUD", "risk_stage": "S4", "recommended_action": "block"},
            {"query": "刷单任务越来越大，我已经垫付了2万，对方说再垫一次就能提现", "is_fraud_relevant": True, "coarse_category": "PART_TIME_JOB_FRAUD", "risk_stage": "S4", "recommended_action": "block"},
            {"query": "我按对方要求扫码转账了，现在联系不上对方了", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S4", "recommended_action": "block"},
            {"query": "对方说我涉嫌洗钱，让我把所有存款转到安全账户", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S4", "recommended_action": "block"},
            # S5 — 损失已发生
            {"query": "我被骗了10万，已经转出去了，现在怎么办", "is_fraud_relevant": True, "coarse_category": "INVESTMENT_FRAUD", "risk_stage": "S5", "recommended_action": "report"},
            {"query": "刷单被骗，损失了5万，对方已经拉黑我了", "is_fraud_relevant": True, "coarse_category": "PART_TIME_JOB_FRAUD", "risk_stage": "S5", "recommended_action": "report"},
            {"query": "网恋对象骗走了我8万，现在消失了", "is_fraud_relevant": True, "coarse_category": "ROMANCE_FRAUD", "risk_stage": "S5", "recommended_action": "report"},
            {"query": "我点了短信里的链接，银行卡里的钱被转走了", "is_fraud_relevant": True, "coarse_category": "PHISHING", "risk_stage": "S5", "recommended_action": "report"},
            # S6 — 二次受害 / 追损诈骗
            {"query": "有人说可以帮我追回被骗的钱，需要先交手续费", "is_fraud_relevant": True, "coarse_category": "RECOVERY_FRAUD", "risk_stage": "S6", "recommended_action": "block"},
            {"query": "警察说可以帮我追回损失，但需要配合再转一笔钱", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S6", "recommended_action": "block"},
            # 补充覆盖更多类型
            {"query": "有人说帮我办理信用卡套现，手续费很低", "is_fraud_relevant": True, "coarse_category": "CREDIT_CARD_FRAUD", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "收到电话说我的社保卡异常，让我去ATM操作", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S3", "recommended_action": "block"},
            {"query": "有人说帮我代购海外商品，让我先付款", "is_fraud_relevant": True, "coarse_category": "SHOPPING_FRAUD", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "对方说我的孩子在学校出事了，需要马上转账", "is_fraud_relevant": True, "coarse_category": "IMPERSONATE_POLICE_GOV", "risk_stage": "S4", "recommended_action": "block"},
            {"query": "有人说帮我刷好评，每单50元，让我先充值", "is_fraud_relevant": True, "coarse_category": "PART_TIME_JOB_FRAUD", "risk_stage": "S2", "recommended_action": "warn"},
            {"query": "收到邮件说我的账号涉及违规，点链接验证", "is_fraud_relevant": True, "coarse_category": "PHISHING", "risk_stage": "S1", "recommended_action": "educate"},
        ]
        # fmt: on
        records = []
        for item in _MATRIX:
            records.append(
                IntentEvalRecord(
                    query=item["query"],
                    is_fraud_relevant=item["is_fraud_relevant"],
                    coarse_category=item["coarse_category"],
                    risk_stage=item["risk_stage"],
                    recommended_action=item["recommended_action"],
                )
            )
        return records

    def get_eval_records(self) -> List[IntentEvalRecord]:
        """返回内置评测集（7×16 矩阵），可被 DSPy 优化器直接消费。"""
        return self.generate_eval_matrix()

