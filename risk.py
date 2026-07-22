"""Explainable, keyword-based financial risk analysis for ASX news."""

import re


class RiskAnalyzer:
    """Score financial risk using weighted ASX-relevant words and phrases."""

    def __init__(self):
        self.maximum_score = 100
        self.title_multiplier = 2.5

        # Phrases are deliberately visible and weighted, keeping the model
        # simple to explain in project documentation and evaluation.
        self.risk_terms = {
            # Severe financial or legal events
            "bankruptcy": 50,
            "insolvency": 45,
            "liquidation": 45,
            "administration": 45,
            "receivership": 45,
            "fraud": 40,
            "accounting scandal": 35,
            "criminal charges": 30,
            "class action": 25,
            "regulatory action": 20,
            "asic investigation": 30,
            "criminal investigation": 30,
            "anti-money laundering": 30,

            # Material company or market risks
            "trading halt": 30,
            "trading suspension": 30,
            "profit warning": 28,
            "earnings downgrade": 28,
            "guidance cut": 27,
            "reduced guidance": 27,
            "guidance withdrawn": 30,
            "forecast cut": 26,
            "lowered outlook": 25,
            "earnings miss": 25,
            "missed expectations": 24,
            "capital raise": 22,
            "capital raising": 22,
            "dilution": 20,
            "impairment": 20,
            "write-down": 20,
            "write-off": 18,
            "debt covenant": 24,
            "default": 30,
            "credit downgrade": 22,
            "investigation": 20,
            "lawsuit": 20,
            "legal action": 20,
            "court case": 18,
            "penalty": 15,
            "fine": 12,
            "downgrade": 18,

            # Financial weakness
            "cash flow problems": 22,
            "cash flow crisis": 25,
            "negative cash flow": 22,
            "cash shortage": 24,
            "cash burn": 20,
            "high debt": 18,
            "debt": 8,
            "loss": 12,
            "net loss": 18,
            "record loss": 22,

            # Negative operating and market signals
            "profit decline": 18,
            "revenue decline": 17,
            "sales decline": 16,
            "margin pressure": 15,
            "cost pressure": 14,
            "weak demand": 16,
            "supply disruption": 18,
            "operational disruption": 18,
            "production delay": 18,
            "production cut": 20,
            "plant closure": 22,
            "mine closure": 22,
            "contract termination": 20,
            "customer loss": 18,

            "shares fell": 15,
            "share price fell": 16,
            "share slump": 18,
            "sell-off": 18,
            "market selloff": 18,
            "price plunge": 25,
            "stock plunge": 25,
            "bear market": 15,

            # Economic risks
            "recession": 12,
            "tariffs": 10,
            "interest rates": 6,
            "currency risk": 10,
            "inflation": 6,

            # Lower-level uncertainty
            "uncertainty": 8,
            "volatile": 8,
            "volatility": 8,
            "headwinds": 10,
            "slowdown": 10,
            "warning": 8,
            "pressure": 6
        }

        # Pre-compile all patterns once at construction time.
        # Each pattern uses word boundaries so partial-word matches
        # (e.g. "fine" inside "define") are never counted.
        self._compiled = {
            phrase: re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")
            for phrase in self.risk_terms
        }

    @staticmethod
    def _article_text(article, field):
        return (article.get(field) or "").lower()

    def _occurrences(self, text, phrase):
        """Count phrase matches without treating part of a word as a match."""
        return len(self._compiled[phrase].findall(text))

    def _score_text(self, text, multiplier=1.0):
        score = 0
        for phrase, weight in self.risk_terms.items():
            hits = self._occurrences(text, phrase)
            if hits == 0:
                continue
            # Cap each individual term at 2 occurrences so that a single
            # repeated word (e.g. "debt" ten times) cannot dominate the
            # total score on its own.
            capped_hits = min(hits, 2)
            score += capped_hits * weight * multiplier
        return score

    def analyse_article(self, article):
        """Return a 0-100 risk score, giving headlines greater importance."""
        title_score = self._score_text(
            self._article_text(article, "title"),
            self.title_multiplier
        )
        description_score = self._score_text(
            self._article_text(article, "description")
        )

        return round(min(title_score + description_score, self.maximum_score), 2)

    def analyse_articles(self, articles):
        """Return the average risk score and each article's score."""
        if not articles:
            return 0.0, []

        article_scores = [
            self.analyse_article(article)
            for article in articles
        ]

        return round(sum(article_scores) / len(article_scores), 2), article_scores
