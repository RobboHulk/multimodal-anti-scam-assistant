"""
build_unified_vector_store.py
=============================
主线官方构建入口：将 text_vectors.jsonl、image_vectors_v2.jsonl、可选的 law_vectors.jsonl
构建为统一 FAISS 索引。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_graph.vector_store.unified_store import UnifiedVectorStore
from shared.config.llm_config import EMBEDDING_DIM, VECTOR_STORE_META_PATH, VECTOR_STORE_PATH

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "knowledge_graph" / "processed_data"
DEFAULT_TEXT_VECTORS = PROCESSED_DATA_DIR / "text_vectors.jsonl"
DEFAULT_IMAGE_VECTORS = PROCESSED_DATA_DIR / "image_vectors_v2.jsonl"
DEFAULT_LAW_VECTORS = PROCESSED_DATA_DIR / "law_vectors.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unified FAISS vector store (text + image + optional law)")
    parser.add_argument("--text-vectors", default=str(DEFAULT_TEXT_VECTORS))
    parser.add_argument("--image-vectors", default=str(DEFAULT_IMAGE_VECTORS))
    parser.add_argument("--law-vectors", default=str(DEFAULT_LAW_VECTORS))
    parser.add_argument("--index-path", default=VECTOR_STORE_PATH)
    parser.add_argument("--meta-path", default=VECTOR_STORE_META_PATH)
    args = parser.parse_args()

    text_vectors_path = Path(args.text_vectors)
    image_vectors_path = Path(args.image_vectors)
    law_vectors_path = Path(args.law_vectors)
    index_path = Path(args.index_path)
    meta_path = Path(args.meta_path)

    missing = [str(p) for p in [text_vectors_path, image_vectors_path] if not p.exists()]
    if missing:
        raise FileNotFoundError(f"构建统一向量库失败，缺少输入文件: {missing}")

    store = UnifiedVectorStore(dim=EMBEDDING_DIM)
    stats = store.build(
        text_vectors_path=text_vectors_path,
        image_vectors_path=image_vectors_path,
        law_vectors_path=law_vectors_path if law_vectors_path.exists() else None,
    )
    store.save(index_path=index_path, meta_path=meta_path)

    print(f"统一向量库已构建: {index_path}")
    print(f"元数据已写入: {meta_path}")
    print(f"text_count: {stats['text_count']}")
    print(f"image_count: {stats['image_count']}")
    print(f"law_count: {stats['law_count']}")
    print(f"index_total: {stats['index_total']}")
    print(f"meta_total: {stats['meta_total']}")


if __name__ == "__main__":
    main()
