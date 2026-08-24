"""共享配置：LLM、Neo4j、外部服务。"""

from __future__ import annotations

import os
from pathlib import Path

# =====================
# 路径基准
# =====================
# 项目根目录（shared/config/ 的上两级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# 与项目仓库同级的 Models 目录（../Models）
_DEFAULT_MODELS_DIR = _PROJECT_ROOT.parent / "Models"

# =====================
# LLM 配置
# =====================
DEFAULT_LLM_PROVIDER = os.getenv("ANTIFRAUD_LLM_PROVIDER", "dashscope")
DEFAULT_LOCAL_MODEL_PATH = os.getenv(
    "ANTIFRAUD_LOCAL_QWEN_PATH",
    str(_DEFAULT_MODELS_DIR / "Qwen2.5-Omni-7B" / "snapshots" / "ae9e1690543ffd5c0221dc27f79834d0294cba00"),
)
# qwen-omni-turbo: 支持文本/图片/音频/视频全模态，与本地 Qwen2.5-Omni-7B 同系列
DEFAULT_DASHSCOPE_MODEL = os.getenv("ANTIFRAUD_DASHSCOPE_TEXT_MODEL", "qwen-omni-turbo")
DEFAULT_DASHSCOPE_MULTIMODAL_MODEL = os.getenv(
    "ANTIFRAUD_DASHSCOPE_MULTIMODAL_MODEL",
    "qwen-omni-turbo",
)
# 当前 unified retrieval 在线检索实际使用的是 `text-embedding-v3` 统一向量空间。
# `DASHSCOPE_MULTIMODAL_EMBEDDING_MODEL` 目前仅保留为后续多模态 embedding 接入预留，
# 尚未进入统一索引的线上查询链路。
DASHSCOPE_EMBEDDING_MODEL = os.getenv("ANTIFRAUD_EMBEDDING_MODEL", "text-embedding-v3")
DASHSCOPE_MULTIMODAL_EMBEDDING_MODEL = os.getenv(
    "ANTIFRAUD_MULTIMODAL_EMBEDDING_MODEL",
    "multimodal-embedding-one-peace-v1",
)
# DashScope `text-embedding-v3` supports 64/128/256/512/768/1024.
EMBEDDING_DIM = int(os.getenv("ANTIFRAUD_EMBEDDING_DIM", "1024"))
VECTOR_STORE_PATH = os.getenv(
    "ANTIFRAUD_VECTOR_STORE_PATH",
    str(_PROJECT_ROOT / "knowledge_graph" / "vector_store" / "unified.index"),
)
VECTOR_STORE_META_PATH = os.getenv(
    "ANTIFRAUD_VECTOR_STORE_META_PATH",
    str(_PROJECT_ROOT / "knowledge_graph" / "vector_store" / "unified_meta.jsonl"),
)
# 检索主链路模式：
# - vector_graph: 默认，仅启用统一向量检索 + 图谱检索
# - hybrid: 启用词法 + 向量 + 图谱
# - lexical_only: 仅词法检索（调试/回归使用）
RETRIEVAL_MODE = os.getenv("ANTIFRAUD_RETRIEVAL_MODE", "vector_graph")

# =====================
# Neo4j 配置
# =====================
# 本地 Docker 容器：docker run -p 7687:7687 neo4j:5.26.0-community
NEO4J_URI = os.getenv("ANTIFRAUD_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("ANTIFRAUD_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("ANTIFRAUD_NEO4J_PASSWORD", "antifraud2026")

# =====================
# 记忆存储配置
# =====================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:antifraud2026@localhost:5432/antifraud")
