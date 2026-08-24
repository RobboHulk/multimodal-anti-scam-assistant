"""硬规则安全引擎。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from intent_recognizer.config import STAGE_ACTION, STAGE_URGENCY
from intent_recognizer.schema import CueSet, IntentInput, RiskStage


@dataclass(frozen=True)
class SafetyDecision:
    rule_name: str
    matched_text: str
    matched_source: str   # "text" | "image" | "audio" | "combined"
    risk_stage: str
    urgency: str
    recommended_action: str
    response: str


@dataclass(frozen=True)
class SafetyRule:
    name: str
    pattern: str
    risk_stage: str
    response: str
    priority: int = 100


DEFAULT_SAFETY_RULES: List[SafetyRule] = [
    SafetyRule(
        name="safe_account_transfer",
        pattern=r"((安全账户|资金清查|洗钱调查).*(转账|转到|汇款|打款|付款)|(转账|转到|汇款|打款|付款).*(安全账户|资金清查|洗钱调查))",
        risk_stage=RiskStage.S4.value,
        response="这高度符合冒充公检法诱导转账特征，请立即停止转账，不要继续沟通，并尽快联系银行与警方。",
        priority=1,
    ),
    SafetyRule(
        name="screen_share_banking",
        pattern=r"(共享屏幕.*银行|银行.*共享屏幕|远程.*银行app|银行app.*远程)",
        risk_stage=RiskStage.S3.value,
        response="对方正在诱导你暴露关键账户操作，请立刻停止共享屏幕或远程控制。",
        priority=2,
    ),
    SafetyRule(
        name="verification_code_leak",
        pattern=r"(验证码.*发给我|把验证码.*给我|短信码.*告诉我)",
        risk_stage=RiskStage.S2.value,
        response="验证码属于核心安全信息，任何索要验证码的行为都应立即中止并核实身份。",
        priority=3,
    ),
    SafetyRule(
        name="forced_app_install",
        pattern=r"(下载.*app.*操作|安装.*软件.*指导|远程协助.*安装)",
        risk_stage=RiskStage.S3.value,
        response="诱导安装陌生软件是典型高危动作，请立即停止下载并检查设备权限。",
        priority=4,
    ),
    SafetyRule(
        name="victim_isolation",
        pattern=r"(不要告诉.*家人|先别报警|保密.*警察|不能告诉任何人)",
        risk_stage=RiskStage.S3.value,
        response="让你与家人或警方隔离，是典型诈骗操控话术，请立即终止沟通并联系可信亲友。",
        priority=5,
    ),
    # ---- 新增规则 ----
    SafetyRule(
        name="qr_code_transfer",
        pattern=r"(扫码.*(转账|付款|汇款)|二维码.*(付款|转账)|扫一扫.*(汇款|付款))",
        risk_stage=RiskStage.S4.value,
        response="通过二维码转账是常见诈骗手段，请立即停止扫码操作，核实对方真实身份。",
        priority=6,
    ),
    SafetyRule(
        name="fake_court_notice",
        pattern=r"(法院传票|检察院通知|涉案冻结|配合调查.*(账户|资金)|公安局.*(通知|传唤))",
        risk_stage=RiskStage.S4.value,
        response="冒充司法机关是高频诈骗手段，真实公检法不会通过电话或网络要求转账，请立即挂断并报警核实。",
        priority=7,
    ),
    SafetyRule(
        name="loan_fee_prepay",
        pattern=r"(放款前.*(手续费|保证金|刷流水)|先交.*(保证金|手续费|押金).*贷款|刷流水.*贷款)",
        risk_stage=RiskStage.S3.value,
        response="正规贷款不会要求放款前预付任何费用，这是典型的贷款诈骗话术，请立即停止操作。",
        priority=8,
    ),
    SafetyRule(
        name="romance_gift_card",
        pattern=r"(礼品卡.*(充值|发给我|号码)|steam.*(卡|充值).*(发给|告诉)|itunes.*(卡|充值))",
        risk_stage=RiskStage.S3.value,
        response="要求购买礼品卡并发送卡号是情感诈骗的常见收款方式，请立即停止并核实对方身份。",
        priority=9,
    ),
]


class SafetyRuleEngine:
    """先于 LLM 执行的安全规则引擎。"""

    def __init__(self, rules: Optional[List[SafetyRule]] = None) -> None:
        self.rules = sorted(rules or DEFAULT_SAFETY_RULES, key=lambda item: item.priority)

    def evaluate(self, intent_input: IntentInput, cues: CueSet) -> Optional[SafetyDecision]:
        sources = {
            "text": intent_input.text or "",
            "image": " ".join(filter(None, [intent_input.image_ocr_text, intent_input.image_caption])),
            "audio": intent_input.audio_text or "",
        }
        combined_text = "\n".join(
            part
            for part in [
                sources["text"],
                sources["image"],
                sources["audio"],
                " ".join(cues.cross_modal_matches),
            ]
            if part
        )
        for rule in self.rules:
            match = re.search(rule.pattern, combined_text, flags=re.IGNORECASE)
            if not match:
                continue
            matched_str = match.group(0)
            # 判断触发来源
            if re.search(rule.pattern, sources["text"], flags=re.IGNORECASE):
                matched_source = "text"
            elif re.search(rule.pattern, sources["image"], flags=re.IGNORECASE):
                matched_source = "image"
            elif re.search(rule.pattern, sources["audio"], flags=re.IGNORECASE):
                matched_source = "audio"
            else:
                matched_source = "combined"
            return SafetyDecision(
                rule_name=rule.name,
                matched_text=matched_str,
                matched_source=matched_source,
                risk_stage=rule.risk_stage,
                urgency=STAGE_URGENCY[rule.risk_stage],
                recommended_action=STAGE_ACTION[rule.risk_stage],
                response=rule.response,
            )
        return None


def heuristic_risk_stage(intent_input: IntentInput, cues: CueSet) -> str:
    """不依赖 LLM 的风险阶段启发式判定。"""
    combined_text = "\n".join(
        part
        for part in [
            intent_input.text,
            intent_input.image_ocr_text,
            intent_input.image_caption,
            intent_input.audio_text,
        ]
        if part
    )

    if re.search(r"(已经转账|被骗了|损失|追回|报警|立案|报案)", combined_text):
        return RiskStage.S5.value
    if re.search(r"(跑分|代收款|代提现吗|洗钱|卡商|帮忙收款)", combined_text):
        return RiskStage.S6.value
    if re.search(r"(转账|转到|汇款|付款|充值|银行app|网银|支付|保证金|押金|定金|解冻费|手续费|先转\d+)", combined_text):
        return RiskStage.S4.value
    if re.search(r"(下载app|安装软件|共享屏幕|远程|扫码|点击链接)", combined_text):
        return RiskStage.S3.value
    if re.search(r"(验证码|身份证|银行卡|个人信息|征信)", combined_text):
        return RiskStage.S2.value
    if re.search(r"(老师带单|兼职|退款|客服|警察|朋友借钱|投资)", combined_text):
        return RiskStage.S1.value
    if cues.total_cue_count() > 0:
        return RiskStage.S1.value
    return RiskStage.S0.value

