-- =====================================================
-- Trend Analyzer for the ASX
-- SQLite Database Schema
-- Author: Karan Attavar
-- =====================================================

CREATE TABLE IF NOT EXISTS analysis_records (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,

    company_name TEXT NOT NULL,

    analysis_date TEXT NOT NULL,

    sentiment_score REAL NOT NULL,

    risk_score REAL NOT NULL,

    sureness_score REAL NOT NULL,

    article_count INTEGER NOT NULL,

    ai_summary TEXT,

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_articles (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    analysis_record_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    description TEXT DEFAULT '',

    source_name TEXT DEFAULT 'Unknown source',

    article_url TEXT DEFAULT '',

    published_at TEXT NOT NULL,

    sentiment_score REAL NOT NULL,

    risk_score REAL NOT NULL,

    sureness_score REAL NOT NULL,

    trustworthiness_score REAL NOT NULL DEFAULT 50,

    FOREIGN KEY (analysis_record_id) REFERENCES analysis_records(id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_articles_published_at
ON analysis_articles(published_at);

CREATE TABLE IF NOT EXISTS ai_conversations (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_messages (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    conversation_id INTEGER NOT NULL,

    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),

    content TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation
ON ai_messages(conversation_id, id);
