"""预处理通用工具。"""

from __future__ import annotations

import re
import unicodedata
from hashlib import md5
from pathlib import Path
from typing import Iterable, List


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_read_text(path: str) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def split_sentences(text: str) -> List[str]:
    normalized = collapse_whitespace(text)
    if not normalized:
        return []
    parts = re.split(r"[。！？!?；;]+", normalized)
    return [p.strip() for p in parts if p.strip()]


def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    hits = []
    for keyword in keywords:
        k = keyword.lower()
        if k and k in lowered:
            hits.append(keyword)
    return hits


def get_preprocess_cache_dir(subdir: str = "") -> Path:
    root = Path.cwd() / ".cache" / "preprocessing"
    target = root / subdir if subdir else root
    target.mkdir(parents=True, exist_ok=True)
    return target


def build_cache_file_path(source_path: str, *, subdir: str, suffix: str, ext: str) -> Path:
    src = Path(source_path)
    digest = md5(str(src.resolve()).encode("utf-8")).hexdigest()[:10]
    stem = src.stem or "input"
    ext_norm = ext if ext.startswith(".") else f".{ext}"
    filename = f"{stem}_{suffix}_{digest}{ext_norm}"
    return get_preprocess_cache_dir(subdir) / filename

