"""
---------------------------------------------------------
Trend Analyzer for the ASX
Author: Karan Attavar

Main Flask Application

This file:
• Creates the Flask app
• Loads configuration
• Registers Blueprints
• Initialises the SQLite database
• Starts the web server

---------------------------------------------------------
"""

from flask import Flask
from config import Config

# Provide a graceful fallback if the app is run without the full dependency stack
try:
    import flask
except ImportError:  # pragma: no cover - handled at runtime
    raise SystemExit("Flask is required to run this application")

# Database
from database.database import initialise_database

# Route Blueprints
from routes.home import home_bp
from routes.analysis import analyse_bp
from routes.history import history_bp
from routes.ai import ai_bp
from routes.settings import settings_bp
from routes.trends import trend_bp


def create_app():
    """
    Application Factory
    """

    app = Flask(__name__)

    # -----------------------------
    # Configuration
    # -----------------------------

    app.config.from_object(Config)

    # -----------------------------
    # Database
    # -----------------------------

    initialise_database()

    # -----------------------------
    # Register Blueprints
    # -----------------------------

    app.register_blueprint(home_bp)

    app.register_blueprint(
        analyse_bp,
        url_prefix="/analyse"
    )

    app.register_blueprint(
        history_bp,
        url_prefix="/history"
    )

    app.register_blueprint(
        trend_bp,
        url_prefix="/trends"
    )

    app.register_blueprint(
        ai_bp,
        url_prefix="/ai"
    )

    app.register_blueprint(
        settings_bp,
        url_prefix="/settings"
    )

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        debug=app.config.get("DEBUG", False),
        host="0.0.0.0",
        port=5000
    )
