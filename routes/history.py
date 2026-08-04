"""
---------------------------------------------------------
Trend Analyzer for the ASX
History Route

Handles searching, displaying, viewing, and deleting 
historical stock analysis records.

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

# Database queries and helpers
from database.database import fetch_all, fetch_one, execute_query

# Analysis statistics and visualization
from analysis.statistics import StatisticsCalculator
from graphs.graph_generator import GraphGenerator

# Initialize Blueprint
history_bp = Blueprint("history", __name__)


@history_bp.route("/")
def list_history():
    """
    Displays a list of all historical analyses.
    Supports optional search filters for tickers, company names, and date ranges.
    """
    search_query = request.args.get("search", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    sql_query = "SELECT * FROM analysis_records WHERE 1=1"
    params = []

    if search_query:
        sql_query += " AND (ticker LIKE ? OR company_name LIKE ?)"
        like_param = f"%{search_query}%"
        params.extend([like_param, like_param])

    if start_date:
        sql_query += " AND analysis_date >= ?"
        params.append(f"{start_date} 00:00:00")

    if end_date:
        sql_query += " AND analysis_date <= ?"
        params.append(f"{end_date} 23:59:59")

    sql_query += " ORDER BY analysis_date DESC"
    records = fetch_all(sql_query, tuple(params))

    # Calculate statistics based on the current filtered dataset
    stats_calc = StatisticsCalculator()
    averages = {
        "sentiment": stats_calc.average_sentiment(records),
        "risk": stats_calc.average_risk(records),
        "sureness": stats_calc.average_sureness(records)
    }

    return render_template(
        "history.html",
        records=records,
        search_query=search_query,
        start_date=start_date,
        end_date=end_date,
        averages=averages
    )


@history_bp.route("/edit-notes/<int:record_id>", methods=["GET", "POST"])
def edit_notes(record_id):
    """
    Allows the user to update notes on a saved analysis record.
    """
    record = fetch_one("SELECT * FROM analysis_records WHERE id = ?", (record_id,))

    if not record:
        flash("The requested record could not be found.", "danger")
        return redirect(url_for("history.list_history"))

    if request.method == "POST":
        updated_notes = request.form.get("notes", "").strip()

        if updated_notes == "":
            flash("Notes cannot be empty. Please enter a comment or explanation.", "warning")
            return render_template("edit_notes.html", record=record)

        try:
            execute_query(
                "UPDATE analysis_records SET notes = ? WHERE id = ?",
                (updated_notes, record_id)
            )
            flash("Record notes updated successfully.", "success")
            return redirect(url_for("history.list_history"))

        except Exception as e:
            flash(f"Database Error: Could not update notes. ({e})", "danger")
            return render_template("edit_notes.html", record=record)

    return render_template("edit_notes.html", record=record)


@history_bp.route("/view/<int:record_id>")
def view_record(record_id):
    """
    Detailed dashboard view of a specific analysis run.
    Generates updated trend graphs for the ticker up to this point in time.
    """
    # 1. Fetch the specific record from the database
    record = fetch_one(
        "SELECT * FROM analysis_records WHERE id = ?", 
        (record_id,)
    )

    if not record:
        flash("The requested analysis record could not be found.", "danger")
        return redirect(url_for("history.list_history"))

    # 2. Use NewsAPI article publication dates for the graph timeline. This
    # keeps the detailed view consistent with the main Trends comparison page.
    ticker_history = fetch_all(
        """
        SELECT
            records.ticker,
            articles.published_at AS analysis_date,
            articles.sentiment_score,
            articles.risk_score,
            articles.sureness_score
        FROM analysis_articles AS articles
        JOIN analysis_records AS records ON records.id = articles.analysis_record_id
        WHERE records.ticker = ? AND records.analysis_date <= ?
        ORDER BY articles.published_at ASC
        """,
        (record["ticker"], record["analysis_date"])
    )

    # 3. Compile statistics and generate trend visualization graphs
    graph_paths = {}
    if len(ticker_history) >= 2:
        try:
            stats_calc = StatisticsCalculator()
            trend_data = stats_calc.trend_data(ticker_history)
            
            # Generate the graphs using your customized Matplotlib wrapper
            generator = GraphGenerator()
            graph_paths = generator.generate_all(trend_data)
        except Exception as e:
            # Fallback gracefully if graph rendering fails
            print(f"[History Error] Could not generate historical trend graphs: {e}")
            flash("Temporary issue rendering trend visualization graphs.", "warning")

    return render_template(
        "graph.html",  # Renders the designated detailed graph/record template
        record=record,
        history_count=len(ticker_history),
        graphs=graph_paths
    )


@history_bp.route("/articles/<int:record_id>")
def view_articles(record_id):
    """Show every article selected for one saved analysis record."""
    record = fetch_one("SELECT * FROM analysis_records WHERE id = ?", (record_id,))
    if not record:
        flash("The requested analysis record could not be found.", "danger")
        return redirect(url_for("history.list_history"))

    articles = fetch_all(
        "SELECT * FROM analysis_articles WHERE analysis_record_id = ? ORDER BY published_at DESC",
        (record_id,)
    )
    return render_template("articles.html", record=record, articles=articles)


@history_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    """
    Deletes an analysis run permanently from the database.
    """
    # Check if record actually exists before attempting deletion
    record = fetch_one("SELECT id, ticker FROM analysis_records WHERE id = ?", (record_id,))
    
    if not record:
        flash("Record not found or has already been deleted.", "warning")
        return redirect(url_for("history.list_history"))

    try:
        execute_query("DELETE FROM analysis_articles WHERE analysis_record_id = ?", (record_id,))
        execute_query("DELETE FROM analysis_records WHERE id = ?", (record_id,))
        flash(f"Successfully deleted analysis record for {record['ticker']}.", "success")
    except Exception as e:
        flash(f"Database Error: Could not delete record. ({e})", "danger")

    return redirect(url_for("history.list_history"))


@history_bp.route("/delete-bulk", methods=["POST"])
def delete_bulk_records():
    """Delete the analysis records selected from the history table."""
    raw_ids = request.form.getlist("record_ids")
    try:
        record_ids = sorted({int(record_id) for record_id in raw_ids})
    except ValueError:
        flash("Invalid record selection.", "danger")
        return redirect(url_for("history.list_history"))

    if not record_ids:
        flash("Select at least one analysis record to delete.", "warning")
        return redirect(url_for("history.list_history"))

    placeholders = ", ".join("?" for _ in record_ids)
    try:
        execute_query(
            f"DELETE FROM analysis_articles WHERE analysis_record_id IN ({placeholders})",
            tuple(record_ids)
        )
        execute_query(
            f"DELETE FROM analysis_records WHERE id IN ({placeholders})",
            tuple(record_ids)
        )
        flash(f"Successfully deleted {len(record_ids)} analysis record(s).", "success")
    except Exception as e:
        flash(f"Database Error: Could not delete selected records. ({e})", "danger")

    return redirect(url_for("history.list_history"))
