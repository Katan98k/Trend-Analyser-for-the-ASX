"""
---------------------------------------------------------
Trend Analyzer for the ASX
Trend Route

Handles the Trend Visualisation page that renders the
combined sentiment, risk, and sureness graphs from
historical ASX analysis records.

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint, render_template, request, flash

from database.database import fetch_all
from analysis.statistics import StatisticsCalculator
from graphs.graph_generator import GraphGenerator

trend_bp = Blueprint("trend", __name__)


@trend_bp.route("/")
def view_trends():
    """Displays the Trend Visualisation page."""
    selected_tickers = [
        ticker.strip().upper()
        for ticker in request.args.getlist("tickers")
        if ticker.strip()
    ]
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Use article publication dates from NewsAPI, not the form submission time.
    query = """
        SELECT
            records.ticker,
            articles.published_at AS analysis_date,
            articles.sentiment_score,
            articles.risk_score,
            articles.sureness_score
        FROM analysis_articles AS articles
        JOIN analysis_records AS records ON records.id = articles.analysis_record_id
        WHERE 1=1
    """
    params = []

    if selected_tickers:
        placeholders = ", ".join("?" for _ in selected_tickers)
        query += f" AND records.ticker IN ({placeholders})"
        params.extend(selected_tickers)

    if start_date:
        query += " AND articles.published_at >= ?"
        params.append(start_date)

    if end_date:
        query += " AND articles.published_at < ?"
        params.append(f"{end_date}T23:59:59.999Z")

    query += " ORDER BY articles.published_at ASC"
    records = fetch_all(query, tuple(params))

    available_tickers = [row[0] for row in fetch_all("SELECT DISTINCT ticker FROM analysis_records ORDER BY ticker ASC")]

    if not records:
        flash("No dated NewsAPI articles are available for the selected criteria. Run a new analysis to build article-based trends.", "warning")
        return render_template(
            "trends.html",
            record=None,
            available_tickers=available_tickers,
            selected_tickers=selected_tickers,
            start_date=start_date,
            end_date=end_date,
            graphs={},
            history_count=0
        )

    if len(records) < 2:
        flash("At least two run records are required to generate trend graphs.", "info")
        return render_template(
            "trends.html",
            record=None,
            available_tickers=available_tickers,
            selected_tickers=selected_tickers,
            start_date=start_date,
            end_date=end_date,
            graphs={},
            history_count=len(records)
        )

    stats_calc = StatisticsCalculator()
    trend_data = stats_calc.trend_data(records)

    graph_paths = {}
    try:
        generator = GraphGenerator()
        graph_paths = generator.generate_all(trend_data)
    except Exception as e:
        print(f"[Trend Error] Could not generate trend graphs: {e}")
        flash("Trend graphs could not be generated at this time.", "danger")

    return render_template(
        "trends.html",
        record=None,
        available_tickers=available_tickers,
        selected_tickers=selected_tickers,
        start_date=start_date,
        end_date=end_date,
        graphs=graph_paths,
        history_count=len(records)
    )
