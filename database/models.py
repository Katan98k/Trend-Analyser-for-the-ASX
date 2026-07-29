"""
---------------------------------------------------------
Trend Analyzer for the ASX

Database Models
---------------------------------------------------------
"""


class AnalysisRecord:
    """
    Represents one stored stock analysis.
    """

    def __init__(
        self,
        ticker,
        company_name,
        analysis_date,
        sentiment_score,
        risk_score,
        sureness_score,
        article_count,
        ai_summary="",
        notes="",
        record_id=None,
        created_at=None
    ):

        self.id = record_id

        self.ticker = ticker.upper()

        self.company_name = company_name

        self.analysis_date = analysis_date

        self.sentiment_score = sentiment_score

        self.risk_score = risk_score

        self.sureness_score = sureness_score

        self.article_count = article_count

        self.ai_summary = ai_summary

        self.notes = notes

        self.created_at = created_at

    def to_tuple(self):
        """
        Converts object into SQLite tuple.
        """

        return (

            self.ticker,

            self.company_name,

            self.analysis_date,

            self.sentiment_score,

            self.risk_score,

            self.sureness_score,

            self.article_count,

            self.ai_summary,

            self.notes
        )

    def __repr__(self):

        return (
            f"<AnalysisRecord "
            f"{self.ticker} "
            f"{self.analysis_date}>"
        )