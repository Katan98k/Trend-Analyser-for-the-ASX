"""
---------------------------------------------------------
Trend Analyzer for the ASX

Sentiment Analysis
Uses TextBlob to calculate a sentiment score 
between 0 and 100.

Author: Karan Attavar
Optimized for High/Low Responsiveness
---------------------------------------------------------
"""

import re

try:
    from textblob import TextBlob
except ImportError:  # pragma: no cover - optional dependency
    TextBlob = None


class SentimentAnalyzer:
    """
    Calculates sentiment scores from news articles.
    """

    def __init__(self):

        self.minimum = 0
        self.maximum = 100

        # Financial keywords used to adjust TextBlob's
        # general English sentiment to better suit ASX news.

        self.negative_terms = [
            "loss", "net loss", "decline", "profit decline",
            "revenue decline", "fell", "drop", "slump",
            "sell-off", "plunge", "price plunge",
            "warning", "profit warning", "downgrade",
            "earnings miss", "missed expectations",
            "lawsuit", "investigation", "fraud",
            "bankruptcy", "insolvency", "liquidation",
            "trading halt", "default", "debt",
            "capital raise", "capital raising",
            "dilution", "weak demand", "recession",
            "inflation", "uncertainty", "headwinds",
            "volatility"
        ]

        self.positive_terms = [
            "profit", "record profit", "growth",
            "strong growth", "surge", "record revenue",
            "beats expectations", "beat expectations",
            "strong earnings", "upgrade",
            "dividend", "special dividend",
            "acquisition", "expansion",
            "contract win", "new contract",
            "raises guidance", "guidance increase",
            "buyback", "share buyback",
            "outperform", "record sales"
        ]

        # Pre-compile word-boundary patterns for each term so that
        # partial-word matches (e.g. "loss" inside "blossom") are
        # never counted.  Patterns are compiled once at construction
        # time and reused across every call to analyse_article.
        self._neg_patterns = [
            re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)")
            for t in self.negative_terms
        ]
        self._pos_patterns = [
            re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)")
            for t in self.positive_terms
        ]

    @staticmethod
    def _combine_text(article):
        """
        Combines the title and description into
        one piece of text.
        """
        title = article.get("title", "")
        description = article.get("description", "")

        return f"{title} {description}".strip()

    @staticmethod
    def _polarity_to_score(polarity):
        """
        Converts TextBlob polarity (-1 to 1) into (0 to 100)
        """
        score = (polarity + 1) * 50
        return round(score, 2)

    def _limit(self, score):
        # Dynamically references instance variables instead of hardcoding
        return max(self.minimum, min(self.maximum, score))

    def analyse_article(self, article):
        """
        Returns one article score with high/low emphasis.
        """
        text = self._combine_text(article)

        if not text or TextBlob is None:
            return 50.0

        # 1. Gather base English polarity
        polarity = TextBlob(text).sentiment.polarity

        lower_text = text.lower()

        # 2. Keyword Frequency Counting using word-boundary regex so that
        #    partial matches (e.g. "loss" inside "blossom") are excluded.
        #    Each term is capped at 3 hits to prevent one repeated phrase
        #    from dominating the adjustment.
        neg_count = sum(
            min(len(pat.findall(lower_text)), 3)
            for pat in self._neg_patterns
        )
        pos_count = sum(
            min(len(pat.findall(lower_text)), 3)
            for pat in self._pos_patterns
        )

        # Scale impact dynamically by how heavily the terms are repeated
        polarity -= neg_count * 0.12
        polarity += pos_count * 0.12

        # 3. Non-Linear Contrast Booster (Combats the "neutral drag")
        # Pushes scores away from 0 (neutral 50) toward the extremes 
        if polarity > 0:
            polarity = polarity ** 0.75
        elif polarity < 0:
            polarity = -((-polarity) ** 0.75)

        # Keep polarity within TextBlob's standard bounds
        polarity = max(-1.0, min(1.0, polarity))

        score = self._polarity_to_score(polarity)

        return self._limit(score)

    def analyse_articles(self, articles):
        """
        Returns:
        overall_score
        individual_scores
        """
        if not articles:
            return 50.0, []

        scores = []
        for article in articles:
            scores.append(self.analyse_article(article))

        overall = round(sum(scores) / len(scores), 2)

        return overall, scores
