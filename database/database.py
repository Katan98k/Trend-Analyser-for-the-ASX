"""
---------------------------------------------------------
Trend Analyzer for the ASX

SQLite Database Manager

Creates safe SQLite connections, initialises the schema, and
provides shared query helpers for all application routes.

Author: Karan Attavar
---------------------------------------------------------
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "database/trend_analyzer.db"
SCHEMA_PATH = "database/schema.sql"
RISK_SCORING_MIGRATION = "risk_score_keyword_coverage_v2"


def get_connection():
    """
    Returns an SQLite connection.
    """

    connection = sqlite3.connect(DATABASE_PATH, timeout=10)

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


def initialise_database():
    """
    Creates the database if required and
    executes the schema.
    """

    Path("database").mkdir(exist_ok=True)

    connection = get_connection()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema:

        connection.executescript(schema.read())

    # Lightweight migrations for databases created before article source and
    # trustworthiness details were introduced.
    article_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analysis_articles)")
    }
    migrations = {
        "description": "TEXT DEFAULT ''",
        "source_name": "TEXT DEFAULT 'Unknown source'",
        "article_url": "TEXT DEFAULT ''",
        "trustworthiness_score": "REAL NOT NULL DEFAULT 50"
    }
    for column, definition in migrations.items():
        if column not in article_columns:
            connection.execute(f"ALTER TABLE analysis_articles ADD COLUMN {column} {definition}")

    _apply_risk_scoring_migration(connection)

    connection.commit()

    connection.close()


def _apply_risk_scoring_migration(connection):
    """Update saved derived scores after expanding risk keyword coverage."""
    already_applied = connection.execute(
        "SELECT 1 FROM app_migrations WHERE name = ?",
        (RISK_SCORING_MIGRATION,)
    ).fetchone()
    if already_applied:
        return

    from analysis.risk import RiskAnalyzer
    from analysis.sureness import SurenessAnalyzer

    risk_analyzer = RiskAnalyzer()
    sureness_analyzer = SurenessAnalyzer()
    records = connection.execute(
        "SELECT id, sentiment_score, article_count FROM analysis_records"
    ).fetchall()

    for record in records:
        articles = connection.execute(
            "SELECT id, title, description, sentiment_score FROM analysis_articles WHERE analysis_record_id = ?",
            (record["id"],)
        ).fetchall()
        if not articles:
            continue

        article_risks = [
            risk_analyzer.analyse_article(dict(article))
            for article in articles
        ]
        overall_risk = round(sum(article_risks) / len(article_risks), 2)
        sureness = sureness_analyzer.calculate(
            sentiment_score=record["sentiment_score"],
            risk_score=overall_risk,
            article_count=record["article_count"]
        )

        connection.execute(
            "UPDATE analysis_records SET risk_score = ?, sureness_score = ? WHERE id = ?",
            (overall_risk, sureness, record["id"])
        )
        for article, risk_score in zip(articles, article_risks):
            article_sureness = 100 - abs(article["sentiment_score"] - risk_score)
            connection.execute(
                "UPDATE analysis_articles SET risk_score = ?, sureness_score = ? WHERE id = ?",
                (risk_score, article_sureness, article["id"])
            )

    connection.execute(
        "INSERT INTO app_migrations (name) VALUES (?)",
        (RISK_SCORING_MIGRATION,)
    )


def reset_database():
    """Permanently clear analysis history and recreate its table."""

    connection = get_connection()
    connection.execute("DROP TABLE IF EXISTS ai_messages")
    connection.execute("DROP TABLE IF EXISTS ai_conversations")
    connection.execute("DROP TABLE IF EXISTS analysis_articles")
    connection.execute("DROP TABLE IF EXISTS analysis_records")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema:
        connection.executescript(schema.read())

    connection.commit()
    connection.close()


def execute_query(query, parameters=()):
    """
    Executes INSERT, UPDATE or DELETE.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(query, parameters)

    connection.commit()

    last_row_id = cursor.lastrowid

    connection.close()

    return last_row_id


def fetch_one(query, parameters=()):
    """
    Returns a single row.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(query, parameters)

    row = cursor.fetchone()

    connection.close()

    return row


def fetch_all(query, parameters=()):
    """
    Returns multiple rows.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(query, parameters)

    rows = cursor.fetchall()

    connection.close()

    return rows
