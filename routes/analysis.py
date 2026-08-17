"""
---------------------------------------------------------
Trend Analyzer for the ASX
Analyse Route

Handles fetching new articles, running analysis engines,
requesting Groq AI summaries, and saving records.

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from uuid import uuid4

# Database Connection and Models
from database.database import execute_query
from database.models import AnalysisRecord

# Analysis Engines
from analysis.sentiment import SentimentAnalyzer
from analysis.risk import RiskAnalyzer
from analysis.sureness import SurenessAnalyzer
from analysis.trustworthiness import TrustworthinessAnalyzer

# API Clients
from api.news_api import NewsAPIClient
from api.groq_api import GroqClient
from api.cache import api_cache
from config import Config

# Initialize Blueprint
analyse_bp = Blueprint("analyse", __name__)

# Initialize Clients & Analyzers
news_client = NewsAPIClient()
groq_client = GroqClient()
sentiment_analyzer = SentimentAnalyzer()
risk_analyzer = RiskAnalyzer()
sureness_analyzer = SurenessAnalyzer()
trustworthiness_analyzer = TrustworthinessAnalyzer()


@analyse_bp.route("/", methods=["GET", "POST"])
def run_analysis():
    """
    Renders the analysis submission form (GET) or processes 
    the incoming stock ticker analysis request (POST).
    """
    if request.method == "POST":
        action = request.form.get("action", "fetch_articles")
        ticker = request.form.get("ticker", "").strip().upper()
        company_name = request.form.get("company_name", "").strip()
        notes = request.form.get("notes", "").strip()

        if action == "fetch_articles":
            if not ticker or not company_name:
                flash("Please enter both a Stock Ticker and a Company Name.", "danger")
                return render_template("analyse.html")

            articles = news_client.get_news(keywords=ticker, company_name=company_name)
            if not articles:
                flash(f"No recent news articles found for '{company_name}' ({ticker}).", "warning")
                return render_template("analyse.html")

            selection_token = uuid4().hex
            api_cache.set(
                f"article_selection:{selection_token}",
                {"ticker": ticker, "company_name": company_name, "notes": notes, "articles": articles},
                Config.CACHE_TIMEOUT
            )
            return render_template(
                "select_articles.html",
                ticker=ticker,
                company_name=company_name,
                notes=notes,
                articles=articles,
                selection_token=selection_token
            )

        if action != "analyse_selected":
            flash("Invalid analysis request.", "danger")
            return redirect(url_for("analyse.run_analysis"))

        pending = api_cache.get(f"article_selection:{request.form.get('selection_token', '')}")
        if not pending:
            flash("The article selection expired. Please search again.", "warning")
            return redirect(url_for("analyse.run_analysis"))

        ticker = pending["ticker"]
        company_name = pending["company_name"]
        notes = pending["notes"]
        try:
            selected_indexes = sorted({int(value) for value in request.form.getlist("article_indexes")})
        except ValueError:
            flash("Invalid article selection.", "danger")
            return redirect(url_for("analyse.run_analysis"))

        articles = [
            pending["articles"][index]
            for index in selected_indexes
            if 0 <= index < len(pending["articles"])
        ]
        article_count = len(articles)
        # Criterion 8 evidence hook: active only in the dedicated VS Code
        # "Criterion 8 Breakpoint Capture" configuration.
        if os.getenv("CRIT8_CAPTURE_BREAKPOINTS") == "1":
            breakpoint()
        if not articles:
            flash("Select at least one article to run an analysis.", "warning")
            return render_template(
                "select_articles.html",
                ticker=ticker,
                company_name=company_name,
                notes=notes,
                articles=pending["articles"],
                selection_token=request.form.get("selection_token", ""),
                selected_indexes=selected_indexes
            )

        # 2. Run Analytics Engines
        # Calculate sentiment (Returns overall score and individual scores list) [cite: 24, 25]
        overall_sentiment, individual_sentiment_scores = sentiment_analyzer.analyse_articles(articles)

        # Calculate risk (Returns overall score and individual scores list) [cite: 17]
        overall_risk, individual_risk_scores = risk_analyzer.analyse_articles(articles)

        # Calculate prediction confidence [cite: 39]
        sureness_score = sureness_analyzer.calculate(
            sentiment_score=overall_sentiment,
            risk_score=overall_risk,
            article_count=article_count
        )

        # 3. Generate structured AI summary using Groq
        ai_summary = generate_groq_analysis_summary(company_name, ticker, articles, overall_sentiment, overall_risk, sureness_score)

        # 4. Save analysis results to the database [cite: 64, 65, 68]
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        record = AnalysisRecord(
            ticker=ticker,
            company_name=company_name,
            analysis_date=analysis_date,
            sentiment_score=overall_sentiment,
            risk_score=overall_risk,
            sureness_score=sureness_score,
            article_count=article_count,
            ai_summary=ai_summary,
            notes=notes
        )

        try:
            # SQL Insert matching the schema structure [cite: 64, 68]
            insert_query = """
                INSERT INTO analysis_records (
                    ticker, company_name, analysis_date, 
                    sentiment_score, risk_score, sureness_score, 
                    article_count, ai_summary, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            record_id = execute_query(insert_query, record.to_tuple())

            # Preserve the dated, per-article scores. Trend graphs use the
            # NewsAPI publication date rather than the time this form was run.
            article_insert_query = """
                INSERT INTO analysis_articles (
                    analysis_record_id, title, description, source_name, article_url,
                    published_at, sentiment_score, risk_score, sureness_score, trustworthiness_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for article, sentiment_score, risk_score in zip(
                articles, individual_sentiment_scores, individual_risk_scores
            ):
                published_at = article.get("publishedAt")
                if not published_at:
                    continue

                article_sureness = 100 - abs(sentiment_score - risk_score)
                execute_query(
                    article_insert_query,
                    (
                        record_id,
                        article.get("title") or "Untitled article",
                        article.get("description") or "",
                        (article.get("source") or {}).get("name") or "Unknown source",
                        article.get("url") or "",
                        published_at,
                        sentiment_score,
                        risk_score,
                        article_sureness,
                        trustworthiness_analyzer.calculate(article)
                    )
                )
            flash(f"Analysis successfully completed and saved for {ticker}!", "success")
            
            # Redirect user back to the dashboard to view the new data
            return redirect(url_for("home.home"))

        except Exception as e:
            flash(f"Database Error: Could not save the analysis record. ({e})", "danger")
            return render_template("analyse.html")

    # Render input form on GET request
    return render_template("analyse.html")


def generate_groq_analysis_summary(company_name, ticker, articles, sentiment, risk, sureness):
    """
    Helper function to prompt Groq for a customized summary of 
    this specific stock run using the fetched article context.
    """
    # Format a quick overview of articles for the LLM context
    articles_context = ""
    for i, art in enumerate(articles[:5], 1):  # Feed top 5 articles to prevent token blowup
        title = art.get("title", "No Title")
        desc = art.get("description", "No Description")
        articles_context += f"[{i}] {title}: {desc}\n\n"

    system_prompt = (
        "You are a professional financial analyst specialising in the Australian Securities Exchange (ASX). "
        "Write in a formal, precise, and concise tone. Do not use slang, colloquialisms, or provide financial advice. "
        "Summarize recent news trends, pointing out key sentiment indicators, risks, and overall outlook."
    )

    user_prompt = (
        f"Please write a brief analyst report summary for {company_name} ({ticker}).\n\n"
        f"Metrics Calculated by our Engine:\n"
        f"- Average Sentiment Score: {sentiment}/100 (0=bearish, 100=bullish)\n"
        f"- Calculated Risk Index: {risk}/100 (0=safe, 100=extreme panic/risk)\n"
        f"- Prediction Confidence (Sureness): {sureness}/100\n\n"
        f"Top News Articles fetched:\n"
        f"{articles_context}\n"
        f"Provide a summary highlighting: why the sentiment/risk is at this level, "
        f"what the primary market drivers are, and a closing analyst perspective."
    )

    # Ask Groq to process this specific run when available.
    ai_response = groq_client.send_request(system_prompt, user_prompt)

    if isinstance(ai_response, str):
        normalized = ai_response.lower()
        error_signals = [
            "error occurred",
            "could not find a valid model",
            "model not configured",
            "model not found",
            "could not connect to groq",
            "groq ai could not",
            "invalid model"
        ]

        if any(signal in normalized for signal in error_signals):
            return local_analysis_summary(
                company_name,
                ticker,
                articles,
                sentiment,
                risk,
                sureness,
                error_message=ai_response
            )

    return ai_response


def local_analysis_summary(company_name, ticker, articles, sentiment, risk, sureness, error_message=None):
    """Fallback summary generated locally when Groq is unavailable."""
    summary_lines = [
        f"Local analysis summary for {company_name} ({ticker}):",
        "",
        f"- Sentiment Score: {sentiment}/100",
        f"- Risk Index: {risk}/100",
        f"- Prediction Confidence: {sureness}/100",
        f"- Articles Analyzed: {len(articles)}",
        "",
        "Key insights:",
        "- The analysis engine has completed sentiment, risk, and confidence scoring.",
        "- Use the numeric scores above as the primary result for this run.",
    ]

    if articles:
        summary_lines.append("- Top articles used for this run:")
        for art in articles[:3]:
            title = art.get("title", "Untitled")
            summary_lines.append(f"  • {title}")

    if error_message:
        summary_lines.extend([
            "",
            "Note: Groq AI was unavailable for this run.",
            f"Reason: {error_message}",
            "The summary above was generated locally instead."
        ])

    return "\n".join(summary_lines)
