"""离线增强链路 smoke 测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from knowledge_graph.graph_builder.neo4j_connector import Neo4jGraphBuilder
from knowledge_graph.graph_builder.qwen_annotation_pipeline import QwenTextAnnotationPipeline
from knowledge_graph.graph_builder.qwen_image_annotation_pipeline import QwenImageAnnotationPipeline


class OfflineEnhancementSmokeTestCase(unittest.TestCase):
    def test_mock_offline_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            processed = root / "processed_data"
            cache = root / "annotation_cache"
            output = root / "output"
            cypher = root / "cypher"
            processed.mkdir()
            cache.mkdir()
            output.mkdir()
            cypher.mkdir()

            (processed / "official_chunks.jsonl").write_text(
                json.dumps(
                    {
                        "chunk_id": "case-1",
                        "case_id": "case-1",
                        "fraud_type": "OTHER_UNKNOWN",
                        "fraud_type_cn": "其他",
                        "text": "客服说订单异常，让我点击链接输入验证码。",
                        "keywords": ["客服", "链接", "验证码"],
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
                        "law_name": "反诈条例",
                        "text": "任何单位和个人不得实施电信网络诈骗。",
                        "hierarchy": "第一章",
                        "article_no": "第一条",
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
                            "file_path": "fake_phishing.png",
                            "fraud_type": "OTHER_UNKNOWN",
                        }
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            text_pipeline = QwenTextAnnotationPipeline(
                processed_data_dir=str(processed),
                output_dir=str(output),
                cache_dir=str(cache),
                version="vtest",
                max_workers=1,
            )
            image_pipeline = QwenImageAnnotationPipeline(
                processed_data_dir=str(processed),
                output_dir=str(output),
                cache_dir=str(cache),
                version="vtest",
            )

            text_pipeline.run(mode="full", use_api=False)
            image_pipeline.run(mode="full", use_api=False)

            builder = Neo4jGraphBuilder(
                processed_data_dir=str(processed),
                output_dir=str(cypher),
                annotation_cache_dir=str(cache),
                version="vtest",
                cache_scope="default",
            )
            summary = builder.build_graph(enhanced=True)

            self.assertTrue((output / "annotation_report_vtest.json").exists())
            self.assertTrue((output / "image_annotation_report_vtest.json").exists())
            self.assertTrue((cypher / "build_graph_enhanced_vtest.cypher").exists())
            self.assertIn("node_counts", summary)
            self.assertGreaterEqual(summary["node_counts"].get("FraudType", 0), 1)
            self.assertIn("relation_counts", summary)


if __name__ == "__main__":
    unittest.main()

