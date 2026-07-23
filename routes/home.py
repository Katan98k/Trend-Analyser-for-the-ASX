"""
---------------------------------------------------------
Trend Analyzer for the ASX
Home Route

Displays the application's main dashboard.

Responsibilities
----------------
• Home page
• Recent analyses
• Dashboard statistics
• Navigation

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint
from flask import render_template

from database.database import fetch_all

from analysis.statistics import StatisticsCalculator

from config import Config


# ---------------------------------------------------------
# Blueprint
# ---------------------------------------------------------

home_bp = Blueprint(
    "home",
    __name__
)


# ---------------------------------------------------------
# Home Page
# ---------------------------------------------------------

@home_bp.route("/")
def home():
    """
    Main dashboard.
    """

    # -------------------------------------
    # Load recent analysis records
    # -------------------------------------

    records = fetch_all(
        """
        SELECT *
        FROM analysis_records
        ORDER BY analysis_date DESC
        LIMIT 10
        """
    )

    # -------------------------------------
    # Statistics
    # -------------------------------------

    statistics = StatisticsCalculator()

    average_sentiment = (
        statistics.average_sentiment(records)
    )

    average_risk = (
        statistics.average_risk(records)
    )

    average_sureness = (
        statistics.average_sureness(records)
    )

    highest_sentiment = (
        statistics.highest_sentiment(records)
    )

    highest_risk = (
        statistics.highest_risk(records)
    )

    lowest_risk = (
        statistics.lowest_risk(records)
    )

    # -------------------------------------
    # Render Dashboard
    # -------------------------------------

    return render_template(

        "dashboard.html",

        records=records,

        average_sentiment=average_sentiment,

        average_risk=average_risk,

        average_sureness=average_sureness,

        highest_sentiment=highest_sentiment,

        highest_risk=highest_risk,

        lowest_risk=lowest_risk,

        disclaimer=Config.DISCLAIMER

    )
