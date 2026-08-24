"""文本预处理：规范化、实体格式统一、分段切分。"""

from __future__ import annotations

import re
from typing import List

from preprocessing.schema import GlobalTextFeatures, TextPreprocessResult, TextSegment
from preprocessing.utils import collapse_whitespace, normalize_unicode, split_sentences

PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MONEY_PATTERN = re.compile(r"\d+(?:\.\d+)?(?:元|块|万|千|百|亿)")
BANK_PATTERN = re.compile(r"(?<!\d)\d{12,19}(?!\d)")

RISK_PATTERNS = ["转账", "验证码", "安全账户", "屏幕共享", "下载", "链接", "银行卡", "密码"]
URGENCY_PATTERNS = ["马上", "立刻", "现在", "紧急", "尽快"]


class TextPreprocessor:
    def preprocess(self, text: str) -> TextPreprocessResult:
        clean = self._normalize_text(text)
        sentences = split_sentences(clean)
        if not sentences and clean:
            sentences = [clean]
        segments = [self._to_segment(idx, sent) for idx, sent in enumerate(sentences)]
        features = self._build_global_features(clean)
        return TextPreprocessResult(clean_text=clean, segments=segments, global_features=features)

    def _normalize_text(self, text: str) -> str:
        normalized = normalize_unicode(text)
        normalized = collapse_whitespace(normalized)
        normalized = self._normalize_entities(normalized)
        return normalized

    @staticmethod
    def _normalize_entities(text: str) -> str:
        text = URL_PATTERN.sub("<URL>", text)
        text = PHONE_PATTERN.sub("<PHONE>", text)
        text = BANK_PATTERN.sub("<BANK_CARD>", text)
        text = MONEY_PATTERN.sub("<MONEY>", text)
        return text

    @staticmethod
    def _to_segment(idx: int, sentence: str) -> TextSegment:
        entities: List[str] = []
        entities.extend(["URL"] if "<URL>" in sentence else [])
        entities.extend(["PHONE"] if "<PHONE>" in sentence else [])
        entities.extend(["BANK_CARD"] if "<BANK_CARD>" in sentence else [])
        entities.extend(["MONEY"] if "<MONEY>" in sentence else [])
        risk = [pattern for pattern in RISK_PATTERNS if pattern in sentence]
        return TextSegment(
            speaker="other",
            timestamp=f"T+{idx}",
            text=sentence,
            entities=entities,
            risk_patterns=risk,
        )

    @staticmethod
    def _build_global_features(clean_text: str) -> GlobalTextFeatures:
        has_transfer = any(k in clean_text for k in ["转账", "汇款", "打款", "收款"])
        has_urgency = any(k in clean_text for k in URGENCY_PATTERNS)
        has_code = "验证码" in clean_text
        return GlobalTextFeatures(
            has_transfer_intent=has_transfer,
            has_urgency=has_urgency,
            has_verification_code_request=has_code,
        )

