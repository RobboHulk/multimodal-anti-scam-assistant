"""
few_shot_examples.py
====================
SHALLOW / DEEP Prompt 的 few-shot 示例库。
由 scripts/run_dspy_optimize.py 自动更新。
"""
from __future__ import annotations

from typing import Any, Dict, List

SHALLOW_FEW_SHOT: List[Dict[str, Any]] = [{'label': '自动优化示例1',
  'input_summary': "用户输入：'你好，今天上海天气怎么样'\\n图像OCR：无\\n音频ASR：无",
  'output': {'is_fraud_relevant': False,
             'coarse_category': 'OTHER_UNKNOWN',
             'confidence': 0.9,
             'reasoning': '基于优化产物导出的示例，风险阶段=S0。'}},
 {'label': '自动优化示例2',
  'input_summary': "用户输入：'有人加我微信说是客服，问我要手机号和验证码'\\n图像OCR：无\\n音频ASR：无",
  'output': {'is_fraud_relevant': True,
             'coarse_category': 'IMPERSONATE_ECOM_CUSTOMER_SERVICE',
             'confidence': 0.9,
             'reasoning': '基于优化产物导出的示例，风险阶段=S2。'}}]

DEEP_FEW_SHOT: List[Dict[str, Any]] = [{'label': '自动优化深度示例1',
  'input_summary': "用户输入：'对方自称公安，让我把钱转到安全账户配合调查'\\n浅层初判：IMPERSONATE_POLICE_GOV, "
                   'confidence=0.90\\n线索：risk_stage=S4',
  'output': {'is_fraud_relevant': True,
             'coarse_category': 'IMPERSONATE_POLICE_GOV',
             'risk_stage': 'S4',
             'recommended_action': 'block',
             'primary_signals': ['优化产物示例'],
             'missing_evidence': ['完整上下文'],
             'clarifying_questions': ['是否还有更多上下文截图或录音？'],
             'confidence': 0.9,
             'reasoning': '1. 关键证据：来自自动优化示例。2. 类型：依据产物标签。3. 阶段：依据产物标签。'}},
 {'label': '自动优化深度示例2',
  'input_summary': "用户输入：'我收到一个投资群链接，说日收益10%，靠谱吗'\\n浅层初判：INVESTMENT_SCAM, "
                   'confidence=0.90\\n线索：risk_stage=S1',
  'output': {'is_fraud_relevant': True,
             'coarse_category': 'INVESTMENT_SCAM',
             'risk_stage': 'S1',
             'recommended_action': 'verify',
             'primary_signals': ['优化产物示例'],
             'missing_evidence': ['完整上下文'],
             'clarifying_questions': ['是否还有更多上下文截图或录音？'],
             'confidence': 0.9,
             'reasoning': '1. 关键证据：来自自动优化示例。2. 类型：依据产物标签。3. 阶段：依据产物标签。'}}]

def format_shallow_few_shot() -> str:
    """返回 SHALLOW Prompt 用的 few-shot 文本块。"""
    lines = ["## 示例（仅供参考，不要照抄）"]
    for ex in SHALLOW_FEW_SHOT:
        lines.append(f"\n### {ex['label']}")
        lines.append(f"输入摘要: {ex['input_summary']}")
        lines.append(f"期望输出: {ex['output']}")
    return "\n".join(lines)

def format_deep_few_shot() -> str:
    """返回 DEEP Prompt 用的 few-shot 文本块。"""
    import json
    lines = ["## 示例（仅供参考，不要照抄）"]
    for ex in DEEP_FEW_SHOT:
        lines.append(f"\n### {ex['label']}")
        lines.append(f"输入摘要: {ex['input_summary']}")
        lines.append(f"期望输出:\n{json.dumps(ex['output'], ensure_ascii=False, indent=2)}")
    return "\n".join(lines)
