"""
---------------------------------------------------------
Trend Analyzer for the ASX
Settings Route

Handles configuring application parameters, flushing the API 
cache, and performing database reset operations.

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

# Central configurations
from config import Config

# API caching utility
from api.cache import api_cache

# Database initialization utilities
from database.database import reset_database as reset_storage, fetch_one


# Initialize Blueprint
settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
def index():
    """
    Renders the settings dashboard displaying current environment variables, 
    key-configurations, and system statuses.
    """
    # Fetch a quick status check of the database (e.g., number of saved records)
    record_count = 0
    try:
        row = fetch_one("SELECT COUNT(*) as count FROM analysis_records")
        if row:
            record_count = row["count"]
    except Exception as e:
        print(f"[Settings Error] Could not connect to database during status check: {e}")
        record_count = "Database Error (Uninitialized or Corrupted)"

    # Formulate configuration states safely to pass to the template
    system_config = {
        "database_path": getattr(Config, "DATABASE", "Unknown"),
        "has_news_key": bool(getattr(Config, "NEWS_API_KEY", None)),
        "has_groq_key": bool(getattr(Config, "GROQ_API_KEY", None) or getattr(Config, "GROK_API_KEY", None)),
        "news_url": getattr(Config, "NEWS_API_URL", "Unknown"),
        "groq_url": getattr(Config, "GROQ_API_URL", "Unknown"),
        "cache_timeout": getattr(Config, "CACHE_TIMEOUT", 300),
        "max_articles": getattr(Config, "MAX_NEWS_ARTICLES", 20),
        "disclaimer": getattr(Config, "DISCLAIMER", ""),
        "db_record_count": record_count
    }

    system_config["groq_model"] = getattr(Config, "GROQ_MODEL", "") or getattr(Config, "GROK_MODEL", "(not set)")
    return render_template(
        "settings.html", 
        config=system_config
    )


@settings_bp.route("/check-groq", methods=["GET"])
def check_groq():
    """Performs a small Groq API diagnostic request and returns status info."""
    from api.groq_api import GroqClient

    client = GroqClient()
    success, message = client.test_connection()
    if success:
        return jsonify({"status": "ok", "message": message})
    return jsonify({"status": "error", "message": message}), 400


@settings_bp.route("/clear-cache", methods=["POST"])
def clear_cache():
    """
    Clears the temporary API cache, forcing the system to pull
    the most up-to-date data on its next run.
    """
    try:
        api_cache.clear()
        flash("System API cache successfully cleared!", "success")
    except Exception as e:
        flash(f"Error clearing cache: {e}", "danger")
        
    return redirect(url_for("settings.index"))


@settings_bp.route("/reset-db", methods=["POST"])
def reset_database():
    """
    Resets the SQLite database back to its initial schema. 
    WARNING: This permanently drops and recreates the analysis table.
    """
    # Double-check confirmation field from form to avoid accidental clicks
    confirm_text = request.form.get("confirm_reset", "").strip().upper()

    if confirm_text != "RESET":
        flash("Database reset aborted. You must type 'RESET' to confirm.", "warning")
        return redirect(url_for("settings.index"))

    try:
        reset_storage()
        flash("Database successfully reset! All historical records have been cleared.", "success")
    except Exception as e:
        flash(f"Critical error resetting database: {e}", "danger")

    return redirect(url_for("settings.index"))
