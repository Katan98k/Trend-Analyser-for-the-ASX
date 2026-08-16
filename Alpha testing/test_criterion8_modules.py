"""Criterion 8 controlled module tests.

These tests exercise the real analysis classes used by the Flask application.
The article inputs are deliberately controlled so the expected behaviour is
repeatable and does not depend on live NewsAPI or Groq results.
These are intended to test some sensitive sections of the code without destroying it.

Run from the project root with:

    python -m unittest tests.test_criterion8_modules -v

The test method names retain the Criterion 8 IDs used in the testing report.
"""

import unittest
from unittest.mock import patch

from analysis.risk import RiskAnalyzer
from analysis.sentiment import SentimentAnalyzer
from analysis.sureness import SurenessAnalyzer
from analysis.trustworthiness import TrustworthinessAnalyzer
from routes import analysis as analysis_route


def controlled_article(
    title,
    description,
    source="Controlled Test Source",
    url="https://example.test/article",
):
    """Build a predictable NewsAPI-shaped article without calling an API."""

    return {
        "title": title,
        "description": description,
        "source": {"name": source},
        "url": url,
        "publishedAt": "2026-08-16T12:00:00Z",
    }


class Criterion8ModuleTester(unittest.TestCase):
    """White-box tests for the app's core analysis calculations."""

    def setUp(self):
        """Create fresh instances of the same analyzers used by the app."""

        self.sentiment = SentimentAnalyzer()
        self.risk = RiskAnalyzer()
        self.sureness = SurenessAnalyzer()
        self.trustworthiness = TrustworthinessAnalyzer()

        self.positive_article = controlled_article(
            "Record profit and strong growth beat expectations",
            "The company reported record revenue, raised guidance and "
            "announced a special dividend.",
        )
        self.negative_article = controlled_article(
            "Bankruptcy warning after record loss and debt default",
            "The company faces fraud investigation, insolvency, a cash flow "
            "crisis, production cuts and a price plunge.",
        )

    def test_t28_groq_failure_uses_local_analysis_fallback(self):
        """T28: a failed Groq response produces a usable local summary."""

        positive_sentiment = self.sentiment.analyse_article(
            self.positive_article
        )
        one_article_sureness = self.sureness.calculate(
            sentiment_score=70,
            risk_score=20,
            article_count=1,
        )

        simulated_error = (
            "Groq AI could not produce a response. Controlled offline "
            "simulation."
        )
        with patch.object(
            analysis_route.groq_client,
            "send_request",
            return_value=simulated_error,
        ):
            summary = analysis_route.generate_groq_analysis_summary(
                "Controlled Company",
                "CTL",
                [self.positive_article],
                positive_sentiment,
                0.0,
                one_article_sureness,
            )

        self.assertTrue(
            summary.startswith(
                "Local analysis summary for Controlled Company (CTL):"
            )
        )
        self.assertIn("Groq AI was unavailable", summary)

    def test_t29_positive_financial_news_scores_100_sentiment(self):
        """T29: strongly positive financial language reaches 100."""

        result = self.sentiment.analyse_article(self.positive_article)

        self.assertEqual(100, result)

    def test_t30_negative_high_risk_news_scores_0_and_100(self):
        """T30: severe negative language gives sentiment 0 and risk 100."""

        sentiment_result = self.sentiment.analyse_article(
            self.negative_article
        )
        risk_result = self.risk.analyse_article(self.negative_article)

        self.assertEqual(0, sentiment_result)
        self.assertEqual(100, risk_result)

    def test_t31_neutral_and_empty_articles_return_safe_defaults(self):
        """T31: neutral or missing text remains bounded and does not crash."""

        neutral_article = controlled_article(
            "Company releases market update",
            "The update describes the reporting timetable.",
        )
        empty_article = controlled_article(
            "",
            "",
            source="",
            url="",
        )

        self.assertEqual(
            50.0,
            self.sentiment.analyse_article(neutral_article),
        )
        self.assertEqual(0, self.risk.analyse_article(neutral_article))
        self.assertEqual(
            50.0,
            self.sentiment.analyse_article(empty_article),
        )
        self.assertEqual(0, self.risk.analyse_article(empty_article))

    def test_t32_recognised_reuters_source_scores_98_trust(self):
        """T32: a recognised, complete Reuters article scores highly."""

        reuters_article = controlled_article(
            "Reuters reports ASX company results",
            "A complete financial report with attributed information.",
            source="Reuters",
            url="https://www.reuters.com/markets/example",
        )

        result = self.trustworthiness.calculate(reuters_article)

        self.assertEqual(98, result)

    def test_t33_unknown_source_scores_below_reuters(self):
        """T33: an unknown source receives a lower trust score of 57."""

        reuters_article = controlled_article(
            "Reuters reports ASX company results",
            "A complete financial report with attributed information.",
            source="Reuters",
            url="https://www.reuters.com/markets/example",
        )
        unknown_article = controlled_article(
            "Independent market commentary",
            "A short article from a source not present in the configured "
            "source tiers.",
            source="Unknown Finance Blog",
            url="http://unknown-finance-blog.test/post",
        )

        known_result = self.trustworthiness.calculate(reuters_article)
        unknown_result = self.trustworthiness.calculate(unknown_article)

        self.assertEqual(57, unknown_result)
        self.assertLess(unknown_result, known_result)

    def test_t34_five_articles_raise_sureness_above_one_article(self):
        """T34: more supporting articles increase prediction sureness."""

        one_article_result = self.sureness.calculate(
            sentiment_score=70,
            risk_score=20,
            article_count=1,
        )
        five_article_result = self.sureness.calculate(
            sentiment_score=70,
            risk_score=20,
            article_count=5,
        )

        self.assertEqual(46.2, one_article_result)
        self.assertEqual(66.0, five_article_result)
        self.assertGreater(five_article_result, one_article_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
