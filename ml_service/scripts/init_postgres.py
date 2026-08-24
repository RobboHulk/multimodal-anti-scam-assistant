"""初始化 PostgreSQL 长期记忆表结构。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.config.llm_config import POSTGRES_DSN

try:
    import psycopg2
except Exception as exc:  # pragma: no cover
    raise RuntimeError("未安装 psycopg2-binary，无法初始化 PostgreSQL") from exc


DDL = """
CREATE TABLE IF NOT EXISTS user_profile (
    user_id VARCHAR(64) PRIMARY KEY,
    age_group VARCHAR(16),
    gender VARCHAR(16),
    occupation VARCHAR(64),
    education VARCHAR(16),
    marital_status VARCHAR(16),
    income_level VARCHAR(16),
    investment_preference VARCHAR(16),
    credit_card_frequency VARCHAR(16),
    online_shopping_frequency VARCHAR(16),
    device_usage VARCHAR(16),
    social_platform_preference VARCHAR(16),
    online_time_distribution VARCHAR(16),
    financial_literacy VARCHAR(16),
    risk_preference VARCHAR(16),
    risk_cognition_level VARCHAR(16),
    anti_fraud_knowledge VARCHAR(16),
    guardian_ids TEXT[],
    historical_fraud_victims BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_event (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(128),
    risk_stage VARCHAR(4),
    scam_type VARCHAR(64),
    risk_score FLOAT,
    confidence FLOAT,
    summary TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_behavior_pattern (
    user_id VARCHAR(64) PRIMARY KEY,
    total_sessions INT DEFAULT 0,
    high_risk_count INT DEFAULT 0,
    most_common_scam_type VARCHAR(64),
    avg_risk_score FLOAT DEFAULT 0.0,
    risk_trend VARCHAR(16),
    last_high_risk_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_device_profile (
    user_id VARCHAR(64),
    device_id VARCHAR(128),
    device_type VARCHAR(32),
    os_version VARCHAR(32),
    app_version VARCHAR(32),
    last_used_at TIMESTAMP DEFAULT NOW(),
    security_settings JSONB,
    PRIMARY KEY (user_id, device_id)
);

CREATE TABLE IF NOT EXISTS user_behavior_timeline (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64),
    event_data JSONB,
    risk_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_event_user_id ON risk_event(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_event_created_at ON risk_event(created_at);
CREATE INDEX IF NOT EXISTS idx_risk_event_risk_stage ON risk_event(risk_stage);
CREATE INDEX IF NOT EXISTS idx_risk_event_scam_type ON risk_event(scam_type);
CREATE INDEX IF NOT EXISTS idx_user_behavior_timeline_user_id ON user_behavior_timeline(user_id);
CREATE INDEX IF NOT EXISTS idx_user_behavior_timeline_event_type ON user_behavior_timeline(event_type);
CREATE INDEX IF NOT EXISTS idx_user_behavior_timeline_created_at ON user_behavior_timeline(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profile_age_group ON user_profile(age_group);
CREATE INDEX IF NOT EXISTS idx_user_profile_financial_literacy ON user_profile(financial_literacy);
CREATE INDEX IF NOT EXISTS idx_user_profile_risk_preference ON user_profile(risk_preference);
CREATE INDEX IF NOT EXISTS idx_user_device_profile_user_id ON user_device_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_user_device_profile_device_id ON user_device_profile(device_id);
"""


def main() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.close()
    print("PostgreSQL 表结构初始化完成")


if __name__ == "__main__":
    main()
