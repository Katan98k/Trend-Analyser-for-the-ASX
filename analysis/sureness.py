"""
---------------------------------------------------------
Trend Analyzer for the ASX

Prediction Sureness Analysis

Calculates a prediction sureness score (0-100) from the
relationship between sentiment, risk, and available data.

Author: Karan Attavar
---------------------------------------------------------
"""


class SurenessAnalyzer:
    """Calculates the confidence (sureness) of an analysis."""

    @staticmethod
    def _clamp(value):
        return max(0, min(100, round(value, 2)))

    def calculate(self, sentiment_score, risk_score, article_count=None):
        """
        Calculates prediction confidence.

        Higher sureness occurs when:
        - sentiment and risk show a strong direction
        - both indicators agree on that direction
        - enough articles support the analysis

        Directional agreement is determined by converting both scores
        to the same "bullish/bearish" scale before comparing them:
        - High sentiment (>50) = bullish signal
        - Low risk (<50)       = bullish signal (calm news)
        When both signals point the same way, confidence is higher.
        When they conflict (bullish sentiment but high risk, or vice
        versa), confidence is reduced to reflect the mixed picture.
        """

        # Convert risk to a sentiment-equivalent scale so that both
        # scores can be compared directionally.
        # risk=20  -> risk_as_sentiment=80  (low risk = bullish)
        # risk=80  -> risk_as_sentiment=20  (high risk = bearish)
        risk_as_sentiment = 100 - risk_score

        # Agreement: how closely do the two signals align in direction?
        # Both bullish -> agreement near 100; one bullish, one bearish -> low.
        agreement = 100 - abs(sentiment_score - risk_as_sentiment)

        # Signal strength: how far each indicator is from neutral (50).
        # A score of 50 carries no information; scores near 0 or 100 do.
        sentiment_strength = abs(sentiment_score - 50) * 2   # 0-100
        risk_strength = abs(risk_score - 50) * 2             # 0-100
        signal_strength = (sentiment_strength + risk_strength) / 2

        # Combine agreement and signal strength.
        # Agreement ensures mixed signals don't falsely inflate sureness.
        # Signal strength ensures neutral scores don't falsely inflate it.
        sureness = (
            agreement * 0.4
            +
            signal_strength * 0.6
        )

        # Reduce confidence when very few articles exist.
        if article_count is not None:
            if article_count <= 1:
                sureness *= 0.70
            elif article_count < 5:
                sureness *= 0.85
            elif article_count >= 10:
                sureness = min(100, sureness * 1.05)

        return self._clamp(sureness)
