"""API 服务 smoke 测试。"""

from __future__ import annotations

import unittest

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None

try:
    from knowledge_graph.rag.api_service import create_app
except Exception:  # pragma: no cover
    create_app = None


@unittest.skipIf(TestClient is None or create_app is None, "fastapi 未安装")
class ApiServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_chat_endpoint_returns_chat_type_zero_for_general_chat(self) -> None:
        response = self.client.post(
            "/api/chat/send",
            json={
                "text": "你好，今天天气怎么样？",
                "session_id": "chat-general-1",
                "userProfile": {
                    "id": 1001,
                    "username": "alice",
                    "ageGroup": 2,
                    "gender": 2,
                    "occupation": "student",
                    "riskPreference": 1,
                    "riskThreshold": 70.0,
                    "interventionStrategy": 1
                }
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload.keys()),
            {"chatType", "riskScore", "scamType", "confidence", "riskAction", "tags", "report", "chatResponse"},
        )
        self.assertEqual(payload["chatType"], 0)
        self.assertEqual(payload["riskScore"], 0.0)
        self.assertEqual(payload["scamType"], "")
        self.assertEqual(payload["tags"], [])
        self.assertTrue(payload["chatResponse"].strip())

    def test_chat_endpoint_returns_chat_type_one_for_risk_case(self) -> None:
        response = self.client.post(
            "/api/chat/send",
            json={
                "text": "对方冒充公安让我把钱转到安全账户",
                "session_id": "chat-risk-1",
                "userProfile": {
                    "id": 1002,
                    "username": "bob",
                    "ageGroup": 2,
                    "gender": 1,
                    "occupation": "engineer",
                    "riskPreference": 1,
                    "riskThreshold": 70.0,
                    "interventionStrategy": 2
                }
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload.keys()),
            {"chatType", "riskScore", "scamType", "confidence", "riskAction", "tags", "report", "chatResponse"},
        )
        self.assertEqual(payload["chatType"], 1)
        self.assertIsInstance(payload["riskScore"], float)
        self.assertGreaterEqual(payload["riskScore"], 0.0)
        self.assertLessEqual(payload["riskScore"], 1.0)
        self.assertTrue(payload["scamType"])
        self.assertIn("## 1. 风险结论", payload["report"])
        self.assertIn("## 4. 防御建议", payload["report"])


if __name__ == "__main__":
    unittest.main()

