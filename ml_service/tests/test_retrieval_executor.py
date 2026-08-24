"""检索执行层（含二跳与重排）测试。"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from knowledge_graph.rag.retrieval_executor import RetrievalExecutor


class RetrievalExecutorTestCase(unittest.TestCase):
    def test_second_hop_and_rerank_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            processed = Path(tmp_dir)
            (processed / "official_chunks.jsonl").write_text(
                json.dumps(
                    {
                        "chunk_id": "doc-1",
                        "fraud_type": "IMPERSONATE_CUSTOMER_SERVICE",
                        "text": "客服说订单异常需要验证码才能解冻账户",
                    },
                    ensure_ascii=False,
                )
                + "\n"
                + json.dumps(
                    {
                        "chunk_id": "doc-2",
                        "fraud_type": "IMPERSONATE_CUSTOMER_SERVICE",
                        "text": "平台售后要求我安装远程控制软件",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (processed / "law_chunks.jsonl").write_text(
                json.dumps(
                    {
                        "chunk_id": "law-1",
                        "law_name": "反诈法条",
                        "text": "冒充客服和索要验证码属于典型诈骗手法",
                        "article_no": "第1条",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (processed / "images_manifest.json").write_text(
                json.dumps(
                    [
                        {
                            "image_id": "img-1",
                            "fraud_type": "IMPERSONATE_CUSTOMER_SERVICE",
                            "ocr_text": "客服中心 验证码",
                            "image_caption": "客服页面",
                            "file_path": "a.png",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            executor = RetrievalExecutor(processed_data_dir=str(processed))
            executor._neo4j_checked = True
            executor._neo4j_driver = None
            executor._expand_second_hop = lambda query_tokens, seed_items, top_k: [
                {
                    "source": "graph_doc",
                    "id": "doc-hop-1",
                    "title": "图谱扩展证据",
                    "snippet": "客服 验证码 安全账户",
                    "score": 0.61,
                    "metadata": {"hop_path": ["doc::doc-1", "type::IMPERSONATE_CUSTOMER_SERVICE", "doc::doc-hop-1"]},
                    "_tokens": {"客服", "验证", "证码"},
                }
            ]
            old_mode = os.environ.get("ANTIFRAUD_RETRIEVAL_MODE")
            os.environ["ANTIFRAUD_RETRIEVAL_MODE"] = "hybrid"
            try:
                evidence = executor.retrieve(
                    query="客服 验证码",
                    target_collections=["knowledge_graph", "law_articles"],
                    top_k=6,
                    second_hop=True,
                )
            finally:
                if old_mode is None:
                    os.environ.pop("ANTIFRAUD_RETRIEVAL_MODE", None)
                else:
                    os.environ["ANTIFRAUD_RETRIEVAL_MODE"] = old_mode

            self.assertGreaterEqual(len(evidence), 2)
            self.assertTrue(any(item.metadata.get("hop_path") for item in evidence))
            self.assertTrue(any("rerank_bonus" in item.metadata for item in evidence))
            scores = [item.score for item in evidence]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_vector_source_is_normalized_and_traced(self) -> None:
        executor = RetrievalExecutor(processed_data_dir=".")

        class _FakeStore:
            def search(self, query_vector=None, query_vec=None, top_k=10):
                return [
                    {
                        "id": "doc-1",
                        "source": "vector_text",
                        "title": "文本证据",
                        "snippet": "验证码 风险 提示",
                        "score": 0.88,
                        "metadata": {"source_file": "demo.jsonl"},
                    },
                    {
                        "id": "img-1",
                        "source": "vector_image",
                        "title": "图片证据 img-1",
                        "snippet": "客服页面 验证码",
                        "score": 0.77,
                        "metadata": {"file_path": "a.png"},
                    },
                ]

        executor._vector_store = _FakeStore()
        executor._vector_store_checked = True
        executor._embed_query = lambda _: [0.1, 0.2, 0.3]

        evidence = executor.retrieve(
            query="验证码",
            target_collections=["knowledge_graph"],
            top_k=4,
            second_hop=False,
        )
        trace = executor.get_last_trace()

        self.assertTrue(any(item.source == "doc" for item in evidence))
        self.assertTrue(any(item.source == "image" for item in evidence))
        self.assertNotIn("vector_text", {item.source for item in evidence})
        self.assertEqual(trace.get("vector_store_loaded"), True)
        self.assertEqual(trace.get("query_embedding_generated"), True)
        self.assertGreaterEqual(trace.get("vector_hit_count", 0), 1)
        self.assertEqual(trace.get("vector_source_distribution", {}).get("vector_text"), 1)

    def test_law_vector_backfill_enters_results_for_law_articles(self) -> None:
        executor = RetrievalExecutor(processed_data_dir=".")

        class _FakeStore:
            def search(self, query_vector, top_k=10):
                return [
                    {
                        "id": "doc-1",
                        "source": "vector_text",
                        "title": "文本证据",
                        "snippet": "客服 验证码 安全账户",
                        "score": 0.92,
                        "metadata": {"source_file": "demo.jsonl"},
                    }
                ]

        executor._vector_store = _FakeStore()
        executor._vector_store_checked = True
        executor._embed_query = lambda _: [0.3, 0.4]
        executor._load_law_vector_index = lambda: [
            {
                "id": "law-1",
                "source": "law",
                "title": "中华人民共和国刑法",
                "snippet": "诈骗公私财物，数额较大的，依法追究刑事责任。",
                "vector": None,
                "metadata": {
                    "law_name": "中华人民共和国刑法",
                    "article_no": "第二百六十六条",
                    "retrieval_channel": "vector",
                    "original_source": "vector_law",
                },
                "_tokens": {"诈骗", "法条"},
            }
        ]

        def _fake_search_law_vectors(*, query_vector, top_k, target_collections):
            return [
                {
                    "source": "law",
                    "id": "law-1",
                    "title": "中华人民共和国刑法",
                    "snippet": "诈骗公私财物，数额较大的，依法追究刑事责任。",
                    "score": 0.86,
                    "metadata": {
                        "law_name": "中华人民共和国刑法",
                        "article_no": "第二百六十六条",
                        "retrieval_channel": "vector",
                        "original_source": "vector_law",
                    },
                    "_tokens": {"诈骗", "法条"},
                }
            ]

        executor._search_law_vectors = _fake_search_law_vectors

        evidence = executor.retrieve(
            query="涉及哪些法律责任和法条",
            target_collections=["law_articles"],
            top_k=4,
            second_hop=False,
        )
        trace = executor.get_last_trace()

        self.assertTrue(any(item.source == "law" for item in evidence))
        self.assertGreaterEqual(trace.get("law_vector_hit_count", 0), 1)
        self.assertEqual(trace.get("vector_source_distribution", {}).get("vector_law"), 1)
        self.assertEqual(trace.get("final_distribution", {}).get("law"), 1)


if __name__ == "__main__":
    unittest.main()
