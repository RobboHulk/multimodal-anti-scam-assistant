"""全链路对话编排测试。"""

from __future__ import annotations

import unittest

from knowledge_graph.rag.chat_orchestrator import ChatOrchestrator
from knowledge_graph.rag.fraud_rag_pipeline import FraudRAGPipeline


class ChatOrchestratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = ChatOrchestrator(pipeline=FraudRAGPipeline(enable_llm=False))

    def test_chat_orchestrator_rewrites_query_and_keeps_state(self) -> None:
        first = self.orchestrator.handle_turn(
            text="有人让我共享屏幕并输入验证码",
            session_id="chat-session-1",
        )
        self.assertIn("retrieval", first.trace)
        second = self.orchestrator.handle_turn(
            text="那我现在该怎么办",
            session_id="chat-session-1",
        )
        self.assertIn("effective_text", second.trace)
        self.assertTrue(len(second.trace["effective_text"]) >= len("那我现在该怎么办"))

    def test_chat_orchestrator_writes_state_once_per_turn(self) -> None:
        session_id = "chat-session-state-once"
        self.orchestrator.handle_turn(
            text="客服让我把验证码发给他",
            session_id=session_id,
        )
        state = self.orchestrator.state_store.get(session_id)
        self.assertEqual(len(state.history), 2)
        self.assertTrue(state.history[0].startswith("用户: "))
        self.assertTrue(state.history[1].startswith("助手: "))


if __name__ == "__main__":
    unittest.main()

