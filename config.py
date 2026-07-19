"""
---------------------------------------------------------
Trend Analyzer for the ASX
Author: Karan Attavar

Configuration File

This file stores all configurable settings for the
application, including:

• API Keys
• Database Location
• Flask Secret Key
• Graph Storage Folder
• Cache Settings

Sensitive information is loaded from the .env file.
---------------------------------------------------------
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv():
        return False

# Load environment variables from .env
load_dotenv()

# If python-dotenv isn't available or didn't populate environment variables,
# attempt a simple manual parse of a local .env file so keys like GROQ_API_KEY
# are available even when the environment loader is missing.
try:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        # Only parse if the key isn't already present
        if not os.getenv('GROQ_API_KEY') and not os.getenv('GROK_API_KEY'):
            with open(env_path, 'r', encoding='utf-8') as _env:
                for line in _env:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and not os.getenv(k):
                        os.environ[k] = v
except Exception:
    # Best-effort fallback; don't fail app startup on .env parse errors
    pass

class Config:
    """
    Central configuration class.
    """

    # -------------------------------------------------
    # Flask Configuration
    # -------------------------------------------------

    SECRET_KEY = os.getenv("SECRET_KEY", "development_secret_key")

    DEBUG = True

    # -------------------------------------------------
    # Database
    # -------------------------------------------------

    DATABASE = "database/trend_analyzer.db"

    # -------------------------------------------------
    # API Keys
    # -------------------------------------------------

    NEWS_API_KEY = os.getenv("NEWS_API_KEY")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL") or os.getenv("GROK_MODEL", "")

    # -------------------------------------------------
    # API URLs
    # -------------------------------------------------

    NEWS_API_URL = "https://newsapi.org/v2/everything"

    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

    # -------------------------------------------------
    # Cache Settings
    # -------------------------------------------------

    CACHE_TIMEOUT = 300      # seconds (5 minutes)

    # -------------------------------------------------
    # Graph Settings
    # -------------------------------------------------

    GRAPH_FOLDER = "static/images/graphs"

    # -------------------------------------------------
    # Application Settings
    # -------------------------------------------------

    MAX_NEWS_ARTICLES = 20

    DEFAULT_LANGUAGE = "en"

    DEFAULT_COUNTRY = "au"

    # -------------------------------------------------
    # Financial Disclaimer
    # -------------------------------------------------

    DISCLAIMER = (
        "This application is an analytical support tool "
        "only and does not provide financial advice. "
        "Users remain responsible for all investment "
        "decisions."
    )