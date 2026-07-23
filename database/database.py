"""
---------------------------------------------------------
Trend Analyzer for the ASX

SQLite Database Manager
---------------------------------------------------------
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = "database/trend_analyzer.db"
SCHEMA_PATH = "database/schema.sql"


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

    connection.commit()

    connection.close()


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
