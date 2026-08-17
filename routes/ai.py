"""
---------------------------------------------------------
Trend Analyzer for the ASX
AI Query Route

Provides an interactive dashboard chat where users can
query Groq AI about aggregated database statistics, trends,
and historical stock analysis records.

Author: Karan Attavar
---------------------------------------------------------
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, make_response

# Database Connection and Queries
from database.database import fetch_all, fetch_one, execute_query

# Statistics Utility
from analysis.statistics import StatisticsCalculator

# AI Client
from api.groq_api import GroqClient

# Initialize Blueprint
ai_bp = Blueprint("ai", __name__)

# Initialize the Groq Client
groq_client = GroqClient()

def create_conversation(title="New conversation"):
    """Create a saved conversation and return its database identifier."""
    return execute_query("INSERT INTO ai_conversations (title) VALUES (?)", (title,))


def conversation_exists(conversation_id):
    """Check whether a conversation identifier exists in local storage."""
    return bool(fetch_one("SELECT id FROM ai_conversations WHERE id = ?", (conversation_id,)))


def save_message(conversation_id, role, content):
    """Persist a chat message and refresh its conversation timestamp."""
    execute_query(
        "INSERT INTO ai_messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content)
    )
    execute_query(
        "UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )


def conversation_context(conversation_id, limit=6):
    """Format the latest saved messages as compact context for Groq."""
    messages = fetch_all(
        "SELECT role, content FROM ai_messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
        (conversation_id, limit)
    )
    if not messages:
        return ""

    ordered_messages = reversed(messages)
    lines = [f"{message['role'].title()}: {message['content']}" for message in ordered_messages]
    return "Recent conversation:\n" + "\n".join(lines) + "\n\n"


def is_groq_error_response(ai_response):
    """Recognise diagnostic text returned when Groq cannot answer normally."""
    if not isinstance(ai_response, str):
        return True

    normalized = ai_response.lower()
    error_signals = [
        "error occurred",
        "could not find a valid model",
        "model is not configured",
        "groq api key is not configured",
        "groq ai could not",
        "unable to connect to groq",
        "an error occurred while connecting to groq",
        "groq ai could not find",
        "could not produce a response",
        "model not found",
        "model not supported",
        "model does not exist",
        "has been decommissioned",
        "no longer supported",
        "unexpected groq response"
    ]
    return any(signal in normalized for signal in error_signals)


def is_saved_data_question(question, records):
    """Only use saved analysis data when the user asks for it."""
    question = question.lower()
    data_terms = ("saved", "record", "portfolio", "ticker", "analysis", "sentiment", "risk", "sureness", "trend", "compare", "average", "lowest", "highest")
    return any(term in question for term in data_terms) or any(
        record["ticker"].lower() in question or record["company_name"].lower() in question
        for record in records
    )


def article_citations(user_question, records, limit=3):
    """Cite selected news articles, never database timestamps, for data claims."""
    question = user_question.lower()
    tickers = [record["ticker"] for record in records if record["ticker"].lower() in question]
    query = """
        SELECT articles.title, articles.source_name
        FROM analysis_articles AS articles
        JOIN analysis_records AS records ON records.id = articles.analysis_record_id
    """
    params = []
    if tickers:
        placeholders = ", ".join("?" for _ in tickers)
        query += f" WHERE records.ticker IN ({placeholders})"
        params.extend(tickers)
    query += " ORDER BY articles.published_at DESC LIMIT ?"
    params.append(limit)
    articles = fetch_all(query, tuple(params))
    if not articles:
        return ""
    cited = "; ".join(f'"{article["title"]}" — {article["source_name"] or "Unknown source"}' for article in articles)
    return f"\n\nArticles consulted: {cited}."


def add_article_citations(response, user_question, records):
    """Append relevant stored article titles when the response lacks citations."""
    if not isinstance(response, str) or "Articles consulted:" in response:
        return response
    return response + article_citations(user_question, records)


def general_katan_response(user_question):
    """Return a safe introductory response when live AI is unavailable."""
    return (
        "I am Katan, your ASX analysis assistant. I can help with general ASX concepts, "
        "or you can ask specifically about your saved analyses, articles, sentiment, risk, or trends."
    )


@ai_bp.route("/", methods=["GET", "POST"])
def ai_query():
    """
    Renders the AI query interface (GET) or processes the user's
    question and returns Groq's data-driven answer (POST).
    """
    if request.method == "POST":
        user_question = request.form.get("question", "").strip()
        conversation_id = request.form.get("conversation_id", type=int)

        if not conversation_id or not conversation_exists(conversation_id):
            conversation_id = create_conversation(user_question[:60] or "New conversation")

        if not user_question:
            return redirect(url_for("ai.ai_query", conversation_id=conversation_id))

        # 1. Fetch all records to build the AI's data context
        records = fetch_all("SELECT * FROM analysis_records ORDER BY analysis_date DESC")

        if records and not is_saved_data_question(user_question, records):
            if groq_client.api_key:
                try:
                    ai_response = groq_client.send_request(
                        "You are Katan, a friendly professional ASX specialist. Respond naturally without mentioning saved data, records, sources, or citations unless the user asks about them. Do not provide financial advice.",
                        conversation_context(conversation_id) + user_question
                    )
                except Exception:
                    ai_response = None
                if is_groq_error_response(ai_response):
                    ai_response = general_katan_response(user_question)
            else:
                ai_response = general_katan_response(user_question)
            save_message(conversation_id, "user", user_question)
            save_message(conversation_id, "assistant", ai_response)
            return redirect(url_for("ai.ai_query", conversation_id=conversation_id))

        if not records:
            # If no saved records exist yet, allow the user to still chat with the AI normally.
            if groq_client.api_key:
                try:
                    ai_response = groq_client.send_request(
                        "You are Katan, a friendly and professional specialist in Australian Securities Exchange (ASX) analysis. "
                        "Be clear, composed, and helpful, like a trusted analytical assistant. Do not use slang, hype, "
                        "or provide financial advice.",
                        conversation_context(conversation_id) + user_question
                    )
                except Exception as e:
                    ai_response = f"An error occurred while getting a response from Groq: {e}"

                if is_groq_error_response(ai_response):
                    ai_response = local_ai_fallback(user_question, records, show_model_hint=True)
            else:
                ai_response = local_ai_fallback(user_question, records, show_model_hint=False)

            save_message(conversation_id, "user", user_question)
            save_message(conversation_id, "assistant", ai_response)
            return redirect(url_for("ai.ai_query", conversation_id=conversation_id))

        # 2. Extract and compile context data using StatisticsCalculator
        stats = StatisticsCalculator()
        
        # Format the database records into a readable, lightweight text block
        formatted_records = []
        for r in records:
            formatted_records.append(
                f"- Record #{r['id']}: Ticker: {r['ticker']}, Company: {r['company_name']}, "
                f"Date: {r['analysis_date']}, Sentiment: {r['sentiment_score']}/100, "
                f"Risk: {r['risk_score']}/100, Sureness: {r['sureness_score']}/100, "
                f"Articles Analyzed: {r['article_count']}"
            )
        
        records_context = "\n".join(formatted_records)

        # Build an aggregated stats summary block
        database_summary_context = (
            f"--- DATABASE SUMMARY METRICS ---\n"
            f"Total Analyses Conducted: {len(records)}\n"
            f"Average Sentiment across all runs: {stats.average_sentiment(records)}/100\n"
            f"Average Risk Index: {stats.average_risk(records)}/100\n"
            f"Average Confidence/Sureness Score: {stats.average_sureness(records)}/100\n\n"
            f"--- DETAILED RUN RECORDS ---\n"
            f"{records_context}"
        )

        # 3. Call Groq with the compiled database context and the user's question
        try:
            ai_response = groq_client.ask_database(
                user_query=conversation_context(conversation_id) + "Current question: " + user_question,
                database_context=database_summary_context
            )
        except Exception:
            ai_response = None

        if is_groq_error_response(ai_response):
            ai_response = local_ai_fallback(user_question, records, show_model_hint=True)
        else:
            ai_response = add_article_citations(ai_response, user_question, records)

        save_message(conversation_id, "user", user_question)
        save_message(conversation_id, "assistant", ai_response)
        return redirect(url_for("ai.ai_query", conversation_id=conversation_id))

    def render_ai_page(conversation_id=None, error=None):
        """Render the selected conversation with cache prevention headers."""
        conversations = fetch_all(
            "SELECT * FROM ai_conversations ORDER BY updated_at DESC, id DESC"
        )
        if conversation_id is None and conversations:
            conversation_id = conversations[0]["id"]

        messages = []
        if conversation_id and conversation_exists(conversation_id):
            messages = fetch_all(
                "SELECT role, content, created_at FROM ai_messages WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,)
            )

        response = make_response(
            render_template(
                "ai_query.html",
                conversations=conversations,
                conversation_id=conversation_id,
                messages=messages,
                error=error
            )
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return render_ai_page(request.args.get("conversation_id", type=int))


@ai_bp.route("/new", methods=["POST"])
def new_conversation():
    """Create an empty saved conversation and open it."""
    conversation_id = create_conversation()
    return redirect(url_for("ai.ai_query", conversation_id=conversation_id))


@ai_bp.route("/delete/<int:conversation_id>", methods=["POST"])
def delete_conversation(conversation_id):
    """Permanently delete a saved Katan conversation and its messages."""
    if not conversation_exists(conversation_id):
        return redirect(url_for("ai.ai_query"))

    execute_query("DELETE FROM ai_messages WHERE conversation_id = ?", (conversation_id,))
    execute_query("DELETE FROM ai_conversations WHERE id = ?", (conversation_id,))
    return redirect(url_for("ai.ai_query"))


def local_ai_fallback(user_question, records, show_model_hint=False):
    """Fallback response when Groq AI is unavailable."""
    question_text = user_question.lower()

    if not records:
        if any(word in question_text for word in ["hello", "hi", "hey", "greetings"]):
            return (
                "Hello. I am Katan, your ASX analysis assistant. No saved analysis data is available yet, "
                "but I can explain sentiment, risk scoring, and the dashboard features."
            )

        if "ticker" in question_text and any(word in question_text for word in ["save", "use", "have", "best"]):
            return (
                "I don't have any tickers saved yet, so I can't compare them directly. "
                "Once you run an analysis, I can tell you which tickers have the lowest risk or highest sentiment."
            )

        if "risk" in question_text:
            return (
                "Risk scoring is a measure of how uncertain or volatile a stock looks based on news sentiment. "
                "A lower score means the position looks steadier, while a higher score suggests more caution."
            )

        if "sentiment" in question_text or "bullish" in question_text or "bearish" in question_text:
            return (
                "Sentiment is all about how positive or negative the news and market tone feel around a stock. "
                "When sentiment is high, the outlook is generally more upbeat; when it is low, the mood is more cautious."
            )

        if "analyse" in question_text or "analysis" in question_text or "summary" in question_text:
            return (
                "Analysis is all about combining sentiment, risk, and confidence into a clear picture of a stock. "
                "I can explain how it works and what the scores mean even before you save your first report."
            )

        if any(word in question_text for word in ["what can", "what do", "what should", "how do"]):
            return (
                "You can ask me things like: 'What does risk mean?', 'How is sentiment calculated?', "
                "or 'How do I interpret my next analysis?'"
            )

        if "world cup" in question_text or "worldcup" in question_text or "who won" in question_text:
            return (
                "I don't have live sports scores, but the FIFA World Cup is the biggest international football tournament. "
                "If you want the latest winner, I recommend checking a current sports news source."
            )

        if "bee" in question_text or "hive" in question_text:
            return (
                "When a bee returns to the hive, it may bring nectar or pollen and share information with other bees. "
                "Bees communicate using body movements and help the colony stay organized."
            )

        generic_replies = [
            "I don't have saved analysis records yet, but I can still explain ASX analysis and market signals. "
            "Try asking about risk vs sentiment, how the dashboard works, or what analysis to run next.",
            "I can still chat about ASX market concepts even without saved data. "
            "Ask me what sentiment means, how risk scores are made, or what your first analysis could look like.",
            "No saved records yet, but I can help you understand the dashboard and prepare your first analysis.",
            "I'm here to explain how the ASX analysis tools work and what the scores show. "
            "Ask me anything about risk, sentiment, or the analysis process."
        ]
        index = sum(ord(c) for c in question_text) % len(generic_replies)
        return generic_replies[index]

    stats = StatisticsCalculator()
    avg_sentiment = stats.average_sentiment(records)
    avg_risk = stats.average_risk(records)
    avg_sureness = stats.average_sureness(records)

    def best_tickers_by(key, op):
        """Find every ticker tied for the requested best score."""
        best_record = op(records, key=lambda r: r[key])
        tickers = sorted({r["ticker"] for r in records if r[key] == best_record[key]})
        return best_record, tickers

    def find_record_by_query():
        """Locate the first saved company explicitly named in the question."""
        for record in records:
            ticker = record["ticker"].lower()
            name = record["company_name"].lower()
            if ticker in question_text or name in question_text:
                return record
        return None

    answer_lines = []
    matched = find_record_by_query()

    if matched:
        sentiment_desc = "positive" if matched["sentiment_score"] >= 50 else "cautious"
        risk_desc = "lower risk" if matched["risk_score"] <= 50 else "higher risk"
        answer_lines.append(
            f"For {matched['ticker']}, I see sentiment at {matched['sentiment_score']}/100 and risk at {matched['risk_score']}/100. "
            f"That suggests a {sentiment_desc} tone with {risk_desc} compared to your saved ASX data."
        )
    elif "lowest" in question_text and "risk" in question_text:
        record, tickers = best_tickers_by("risk_score", min)
        answer_lines.append(
            f"From your saved data, the lowest risk score is {record['risk_score']}/100. "
            f"That applies to {', '.join(tickers)}."
        )
    elif "highest" in question_text and "sentiment" in question_text:
        record, tickers = best_tickers_by("sentiment_score", max)
        answer_lines.append(
            f"Looking at the saved records, the strongest sentiment is {record['sentiment_score']}/100. "
            f"The ticker(s) with that score are {', '.join(tickers)}."
        )
    elif "risk" in question_text:
        low_record, low_tickers = best_tickers_by("risk_score", min)
        answer_lines.append(
            f"Your average risk across saved analyses is {avg_risk}/100. "
            f"The safest ticker(s) right now are {', '.join(low_tickers)} with {low_record['risk_score']}/100 risk."
        )
    elif "sentiment" in question_text:
        high_record, high_tickers = best_tickers_by("sentiment_score", max)
        answer_lines.append(
            f"Your average sentiment across saved analyses is {avg_sentiment}/100. "
            f"The most positive ticker(s) are {', '.join(high_tickers)} with {high_record['sentiment_score']}/100 sentiment."
        )
    elif any(term in question_text for term in ["average", "mean", "overall"]):
        answer_lines.append(
            f"Here's a quick local summary from {len(records)} saved analyses:\n"
            f"- Average sentiment: {avg_sentiment}/100\n"
            f"- Average risk: {avg_risk}/100\n"
            f"- Average sureness: {avg_sureness}/100"
        )
    elif any(term in question_text for term in ["trend", "summary", "overview", "analysis", "analyse", "article"]):
        low_record, low_tickers = best_tickers_by("risk_score", min)
        high_record, high_tickers = best_tickers_by("sentiment_score", max)
        answer_lines.append(
            f"From the saved data, the average sentiment is {avg_sentiment}/100 and average risk is {avg_risk}/100. "
            f"The lowest risk ticker(s) are {', '.join(low_tickers)} at {low_record['risk_score']}/100, "
            f"and the most bullish ticker(s) are {', '.join(high_tickers)} at {high_record['sentiment_score']}/100."
        )
    else:
        ticker_names = ", ".join(sorted({r["ticker"] for r in records}))
        answer_lines.append(
            f"I can work with your saved ASX tickers: {ticker_names}. "
            f"Try asking for the lowest risk ticker, the highest sentiment, averages, or a trend summary."
        )

    answer_lines.append("")
    if show_model_hint:
        answer_lines.append(
            "I'm answering from the records I have locally while Groq reconnects."
        )
    else:
        answer_lines.append(
            "I'm answering from the records I have locally right now. "
            "If you'd like, I can still chat about general topics or help you prepare your first ASX analysis."
        )

    return "\n".join(answer_lines)


@ai_bp.route("/api/chat", methods=["POST"])
def ai_chat_api():
    """
    Optional API endpoint supporting AJAX-based chat requests.
    Useful if you want to make the chat page feel highly responsive 
    without refreshing the entire page.
    """
    data = request.get_json() or {}
    user_question = data.get("question", "").strip()
    conversation_id = data.get("conversation_id")

    try:
        conversation_id = int(conversation_id) if conversation_id else None
    except (TypeError, ValueError):
        conversation_id = None

    if not conversation_id or not conversation_exists(conversation_id):
        conversation_id = create_conversation(user_question[:60] or "New conversation")

    if not user_question:
        return jsonify({"error": "Question is empty"}), 400

    records = fetch_all("SELECT * FROM analysis_records ORDER BY analysis_date DESC")
    if records and not is_saved_data_question(user_question, records):
        if groq_client.api_key:
            try:
                ai_response = groq_client.send_request(
                    "You are Katan, a friendly professional ASX specialist. Respond naturally without mentioning saved data, records, sources, or citations unless the user asks about them. Do not provide financial advice.",
                    conversation_context(conversation_id) + user_question
                )
            except Exception:
                ai_response = None
            if is_groq_error_response(ai_response):
                ai_response = general_katan_response(user_question)
        else:
            ai_response = general_katan_response(user_question)
        save_message(conversation_id, "user", user_question)
        save_message(conversation_id, "assistant", ai_response)
        return jsonify({"response": ai_response, "conversation_id": conversation_id})

    if not records:
        if groq_client.api_key:
            try:
                ai_response = groq_client.send_request(
                    "You are Katan, a friendly and professional specialist in Australian Securities Exchange (ASX) analysis. "
                    "Be clear, composed, and helpful. Do not use slang, hype, or provide financial advice.",
                    conversation_context(conversation_id) + user_question
                )
            except Exception:
                ai_response = None

            if is_groq_error_response(ai_response):
                ai_response = local_ai_fallback(user_question, records)
        else:
            ai_response = local_ai_fallback(user_question, records)

        save_message(conversation_id, "user", user_question)
        save_message(conversation_id, "assistant", ai_response)
        return jsonify({"response": ai_response, "conversation_id": conversation_id})

    stats = StatisticsCalculator()
    
    # Compile records into a compact text-only structure
    formatted_records = [
        f"Record #{r['id']}: Ticker: {r['ticker']}, Sentiment: {r['sentiment_score']}, Risk: {r['risk_score']}"
        for r in records
    ]
    records_context = "; ".join(formatted_records)

    database_context = (
        f"Total Runs: {len(records)}. "
        f"Averages: Sentiment={stats.average_sentiment(records)}, Risk={stats.average_risk(records)}. "
        f"Records: {records_context}"
    )

    try:
        ai_response = groq_client.ask_database(
            conversation_context(conversation_id) + "Current question: " + user_question,
            database_context
        )
    except Exception:
        ai_response = None

    if is_groq_error_response(ai_response):
        ai_response = local_ai_fallback(user_question, records, show_model_hint=True)
    else:
        ai_response = add_article_citations(ai_response, user_question, records)

    save_message(conversation_id, "user", user_question)
    save_message(conversation_id, "assistant", ai_response)
    return jsonify({"response": ai_response, "conversation_id": conversation_id})
