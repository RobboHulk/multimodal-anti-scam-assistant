"""
build_image_embeddings.py
=========================
对 images_annotated_v2.0.0.jsonl 做文本化向量生成，输出到 image_vectors_v2.jsonl。
统一使用 DashScope text-embedding-v3 生成 1024 维，便于与文本向量库合并。
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Dict, List

from dashscope import TextEmbedding
from requests.exceptions import RequestException, SSLError

from shared.config.llm_config import DASHSCOPE_EMBEDDING_MODEL, EMBEDDING_DIM

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "knowledge_graph" / "processed_data"
INPUT_PATH = PROCESSED_DATA_DIR / "images_annotated_v2.0.0.jsonl"
LEGACY_IMAGE_VECTOR_PATH = PROCESSED_DATA_DIR / "image_vectors.jsonl"
OUTPUT_PATH = PROCESSED_DATA_DIR / "image_vectors_v2.jsonl"
DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 10
DEFAULT_WORKERS = 4
SLEEP_SECONDS = 0.2
MAX_RETRIES = 5
RETRY_BASE_SECONDS = 1.0
MAX_INPUT_LENGTH = 8000


def load_legacy_clip_map() -> Dict[str, List[float]]:
    if not LEGACY_IMAGE_VECTOR_PATH.exists():
        return {}
    mapping: Dict[str, List[float]] = {}
    with open(LEGACY_IMAGE_VECTOR_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            image_id = str(item.get("image_id", "")).strip()
            vector = item.get("vector", [])
            if image_id and isinstance(vector, list):
                mapping[image_id] = vector
    return mapping


def load_done_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    done = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            image_id = str(item.get("image_id", "")).strip()
            if image_id:
                done.add(image_id)
    return done


def _truncate_by_budget(parts: List[str], max_length: int) -> str:
    kept: List[str] = []
    used = 0
    for part in parts:
        if not part:
            continue
        separator_len = 1 if kept else 0
        remaining = max_length - used - separator_len
        if remaining <= 0:
            break
        if len(part) <= remaining:
            kept.append(part)
            used += separator_len + len(part)
            continue
        if remaining > 3:
            kept.append(part[: remaining - 3] + "...")
            used += separator_len + remaining
        break
    return "\n".join(kept)


def build_text(item: Dict) -> str:
    evidence_points = item.get("evidence_points", [])
    if not isinstance(evidence_points, list):
        evidence_points = [str(evidence_points)] if evidence_points else []
    parts = [
        str(item.get("original_fraud_type", "")).strip(),
        str(item.get("primary_scam_type", "")).strip(),
        " ".join(str(x) for x in evidence_points),
        str(item.get("image_caption", "")).strip(),
        str(item.get("ocr_text", "")).strip(),
        str(item.get("qwen_reason", "")).strip(),
    ]
    return _truncate_by_budget(parts, MAX_INPUT_LENGTH)


def embed_batch(texts: List[str], batch_idx: int) -> List[List[float]]:
    if batch_idx == 0:
        print(f"[batch {batch_idx}] 准备发起首批 image embedding 请求，文本数: {len(texts)}", flush=True)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = TextEmbedding.call(
                model=DASHSCOPE_EMBEDDING_MODEL,
                input=texts,
                dimension=EMBEDDING_DIM,
            )
            if batch_idx == 0:
                print(f"[batch {batch_idx}] 首批 image embedding 请求已返回，开始解析结果", flush=True)
            if response.status_code != 200:
                raise RuntimeError(f"DashScope embedding error: {response.code} {response.message}")
            embeddings = response.output.get("embeddings", [])
            return [item["embedding"] for item in embeddings]
        except (SSLError, RequestException) as exc:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"batch {batch_idx} 网络请求连续失败 {MAX_RETRIES} 次，最后错误: {exc}"
                ) from exc
            wait_seconds = RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            print(
                f"[batch {batch_idx}] 第 {attempt} 次网络请求失败: {exc.__class__.__name__}: {exc}，"
                f"{wait_seconds:.1f}s 后重试",
                flush=True,
            )
            time.sleep(wait_seconds)


def _embed_payload(batch_idx: int, batch: List[Dict], legacy_clip_map: Dict[str, List[float]]) -> List[Dict]:
    texts = [build_text(item) for item in batch]
    if batch_idx == 0:
        for text_idx, text in enumerate(texts):
            if len(text) >= MAX_INPUT_LENGTH:
                print(
                    f"[batch {batch_idx}] 第 {text_idx} 条图像文本过长，已裁剪到 {len(text)} 字符以内",
                    flush=True,
                )
    vectors = embed_batch(texts, batch_idx)
    payloads = []
    for item, vector in zip(batch, vectors):
        image_id = str(item.get("image_id", "")).strip()
        payloads.append(
            {
                "image_id": image_id,
                "file_path": item.get("file_path", ""),
                "resolved_file_path": item.get("resolved_file_path", ""),
                "original_fraud_type": item.get("original_fraud_type", ""),
                "primary_scam_type": item.get("primary_scam_type", ""),
                "ocr_text": item.get("ocr_text", ""),
                "image_caption": item.get("image_caption", ""),
                "evidence_points": item.get("evidence_points", []),
                "qwen_reason": item.get("qwen_reason", ""),
                "tag_confidence": item.get("tag_confidence", 0.0),
                "vector": vector,
                "legacy_clip_vector": legacy_clip_map.get(image_id, []),
            }
        )
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser(description="Build image text embeddings with DashScope")
    parser.add_argument("--input", default=str(INPUT_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help="并发线程数（有界并发），建议 2~4")
    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        raise RuntimeError("未设置 DASHSCOPE_API_KEY")

    input_path = Path(args.input)
    output_path = Path(args.output)
    batch_size = min(args.batch_size, MAX_BATCH_SIZE)
    workers = max(1, args.workers)
    if args.batch_size > MAX_BATCH_SIZE:
        print(f"DashScope image embedding 单次最多处理 {MAX_BATCH_SIZE} 条，batch-size 已自动调整为 {batch_size}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    legacy_clip_map = load_legacy_clip_map()
    done_ids = load_done_ids(output_path)
    print(f"已存在图片向量: {len(done_ids)} 条")
    print(f"Embedding 模型: {DASHSCOPE_EMBEDDING_MODEL}，维度: {EMBEDDING_DIM}，batch-size: {batch_size}，workers: {workers}")

    items = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            image_id = str(item.get("image_id", "")).strip()
            if not image_id or image_id in done_ids:
                continue
            items.append(item)
    print(f"待处理图片: {len(items)} 条")

    total = len(items)
    processed = 0
    batches = [items[idx: idx + batch_size] for idx in range(0, total, batch_size)]
    print(f"批次数: {len(batches)}，执行方式: 有界并发")

    with open(output_path, "a", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            next_batch_idx = 0
            future_to_batch_idx = {}

            while next_batch_idx < len(batches) and len(future_to_batch_idx) < workers:
                future = executor.submit(_embed_payload, next_batch_idx, batches[next_batch_idx], legacy_clip_map)
                future_to_batch_idx[future] = next_batch_idx
                next_batch_idx += 1

            while future_to_batch_idx:
                done, _ = wait(future_to_batch_idx, return_when=FIRST_COMPLETED)
                for future in done:
                    batch_idx = future_to_batch_idx.pop(future)
                    payloads = future.result()
                    for payload in payloads:
                        out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                    out.flush()
                    processed += len(payloads)
                    print(f"[{processed}/{total}] batch {batch_idx} 已完成", flush=True)
                    time.sleep(SLEEP_SECONDS)

                    if next_batch_idx < len(batches):
                        next_future = executor.submit(_embed_payload, next_batch_idx, batches[next_batch_idx], legacy_clip_map)
                        future_to_batch_idx[next_future] = next_batch_idx
                        next_batch_idx += 1

    print(f"\n图片向量化完成: {output_path}")


if __name__ == "__main__":
    main()
