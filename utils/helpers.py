"""
---------------------------------------------------------
Trend Analyzer for the ASX
Helper Utilities

Contains reusable formatting, parsing, and text cleaning
functions for views and templates.

Author: Karan Attavar
---------------------------------------------------------
"""

from datetime import datetime


def format_percentage(value):
    """
    Formats a raw number or float to a clean percentage string.
    Example: 84.321 -> '84.3%'
    """
    try:
        val = float(value)
        return f"{val:.1f}%"
    except (ValueError, TypeError):
        return "0.0%"


def truncate_text(text, max_length=150):
    """
    Truncates a long text snippet (like an article description or AI summary)
    for clean UI rendering in tables or dashboard cards.
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_date_string(date_str, output_format="%d %b %Y, %I:%M %p"):
    """
    Parses database timestamp strings and formats them into readable Australian formats.
    Example: '2026-07-17 11:42:16' -> '17 Jul 2026, 11:42 AM'
    """
    if not date_str:
        return "N/A"
    
    # Try common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue
            
    return date_str  # Return original if parsing fails


def get_sentiment_label(score):
    """
    Returns a colored Bootstrap CSS class and text label based on the sentiment score (0-100).
    """
    try:
        val = float(score)
    except (ValueError, TypeError):
        return "Neutral", "secondary"

    if val >= 70:
        return "Highly Bullish", "success"
    elif val >= 55:
        return "Mildly Bullish", "info"
    elif val >= 45:
        return "Neutral", "secondary"
    elif val >= 30:
        return "Mildly Bearish", "warning"
    else:
        return "Highly Bearish", "danger"