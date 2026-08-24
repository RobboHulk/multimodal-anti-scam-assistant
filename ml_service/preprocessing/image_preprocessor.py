"""图片预处理：质量增强、OCR、页面识别、风险信号提取。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from preprocessing.ocr_client import BaseOCRClient, create_ocr_client
from preprocessing.schema import ImagePreprocessResult, OCRBlock
from preprocessing.utils import build_cache_file_path, keyword_hits

PAGE_PATTERNS = {
    "bank_transfer_page": ["转账", "收款", "银行卡", "到账"],
    "chat_page": ["聊天", "消息", "客服", "对话"],
    "download_page": ["下载", "安装", "apk", "应用"],
    "login_page": ["登录", "验证码", "账户", "密码"],
}

RISK_SIGNALS = [
    "安全账户",
    "验证码",
    "转账",
    "屏幕共享",
    "下载",
    "银行卡",
    "点击链接",
]

OBJECT_KEYWORDS = {
    "二维码": ["二维码", "收款码", "扫码"],
    "转账按钮": ["转账", "立即支付", "确认付款"],
    "验证码输入框": ["验证码", "短信码"],
}


class ImagePreprocessor:
    def __init__(self, *, ocr_client: BaseOCRClient | None = None) -> None:
        self.ocr_client = ocr_client or create_ocr_client()

    def preprocess(self, image_path: str) -> ImagePreprocessResult:
        p = Path(image_path)
        if not p.exists():
            return ImagePreprocessResult(
                enhanced_image_path=image_path,
                status="skipped",
                source_model="image_preprocessor",
                error_code="IMAGE_FILE_NOT_FOUND",
                error_message=f"image file not found: {image_path}",
                warnings=["IMAGE_FILE_NOT_FOUND"],
            )

        enhanced_path = self._enhance_image(image_path)
        structured = self.ocr_client.extract_structured(enhanced_path)
        ocr_text = str(structured.get("ocr_text", ""))
        block_dicts = list(structured.get("ocr_blocks", []))
        ocr_blocks = [self._to_ocr_block(item) for item in block_dicts]
        page_type = str(structured.get("page_type") or self._detect_page_type(ocr_text, ocr_blocks))
        objects = self._merge_items(
            list(structured.get("objects", [])),
            self._detect_objects(ocr_text),
        )
        risk_signals = self._merge_items(
            list(structured.get("risk_signals", [])),
            keyword_hits(ocr_text, RISK_SIGNALS),
            self._risk_signals_from_layout(page_type, ocr_blocks),
        )

        return ImagePreprocessResult(
            ocr_text=ocr_text,
            ocr_blocks=ocr_blocks,
            page_type=page_type,
            objects=objects,
            risk_signals=risk_signals,
            enhanced_image_path=enhanced_path,
            status=str(structured.get("status", "ok") or "ok"),
            source_model=str(structured.get("source_model", "paddleocr_vl_local")),
            error_code=str(structured.get("error_code", "")),
            error_message=str(structured.get("error_message", "")),
            warnings=list(structured.get("warnings", [])),
        )

    def _enhance_image(self, image_path: str) -> str:
        """轻量图像增强，依赖 PIL 可选。"""
        try:
            from PIL import Image, ImageEnhance
        except ImportError:
            return image_path

        src = Path(image_path)
        dst = build_cache_file_path(image_path, subdir="image", suffix="enhanced", ext=".jpg")
        try:
            img = Image.open(src).convert("RGB")
            width, height = img.size
            min_side = min(width, height)
            if min_side < 720:
                scale = 720 / float(min_side)
                img = img.resize((int(width * scale), int(height * scale)))
            img = ImageEnhance.Contrast(img).enhance(1.15)
            img = ImageEnhance.Sharpness(img).enhance(1.1)
            img.save(dst, format="JPEG", quality=92)
            return str(dst)
        except Exception:
            return image_path

    @staticmethod
    def _to_ocr_block(item: dict) -> OCRBlock:
        return OCRBlock(
            text=str(item.get("text", "")),
            bbox=list(item.get("bbox", [])),
            confidence=float(item.get("confidence", 0.0)),
        )

    @staticmethod
    def _detect_page_type(ocr_text: str, ocr_blocks: List[OCRBlock]) -> str:
        lowered = (ocr_text or "").lower()
        best_type = "unknown_page"
        best_score = 0
        for page_type, patterns in PAGE_PATTERNS.items():
            score = sum(1 for p in patterns if p.lower() in lowered)
            if score > best_score:
                best_type = page_type
                best_score = score
        if best_type == "unknown_page" and ocr_blocks:
            # 简单 layout 先验：金额/银行卡等高频文本 + 多块布局，优先判为转账页面
            money_like = sum(1 for block in ocr_blocks if any(token in block.text for token in ["元", "￥", "收款", "转账"]))
            if money_like >= 2:
                best_type = "bank_transfer_page"
        return best_type

    @staticmethod
    def _detect_objects(ocr_text: str) -> List[str]:
        lowered = (ocr_text or "").lower()
        hits: List[str] = []
        for name, patterns in OBJECT_KEYWORDS.items():
            if any(pattern.lower() in lowered for pattern in patterns):
                hits.append(name)
        return hits

    @staticmethod
    def _risk_signals_from_layout(page_type: str, ocr_blocks: List[OCRBlock]) -> List[str]:
        risks: List[str] = []
        if page_type == "bank_transfer_page":
            risks.append("疑似资金页面")
        if len(ocr_blocks) >= 6:
            risks.append("信息密集页面")
        if any("验证码" in block.text for block in ocr_blocks):
            risks.append("验证码相关操作")
        return risks

    @staticmethod
    def _merge_items(*groups: List[str]) -> List[str]:
        merged: List[str] = []
        seen = set()
        for group in groups:
            for item in group:
                key = str(item).strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                merged.append(key)
        return merged

