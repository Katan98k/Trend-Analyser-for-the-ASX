"""
---------------------------------------------------------
Trend Analyzer for the ASX

Statistics

Provides reusable statistical calculations for
historical analysis and graph generation.

Author: Karan Attavar
---------------------------------------------------------
"""

from statistics import mean


class StatisticsCalculator:
    """
    Performs statistical calculations on
    historical analysis records.
    """

    @staticmethod
    def average_sentiment(records):

        if not records:
            return 0.0

        return round(

            mean(

                record["sentiment_score"]

                for record in records

            ),

            2

        )

    @staticmethod
    def average_risk(records):

        if not records:
            return 0.0

        return round(

            mean(

                record["risk_score"]

                for record in records

            ),

            2

        )

    @staticmethod
    def average_sureness(records):

        if not records:
            return 0.0

        return round(

            mean(

                record["sureness_score"]

                for record in records

            ),

            2

        )

    @staticmethod
    def highest_sentiment(records):

        if not records:
            return None

        return max(

            records,

            key=lambda record: record["sentiment_score"]

        )

    @staticmethod
    def highest_risk(records):

        if not records:
            return None

        return max(

            records,

            key=lambda record: record["risk_score"]

        )

    @staticmethod
    def lowest_risk(records):

        if not records:
            return None

        return min(

            records,

            key=lambda record: record["risk_score"]

        )

    @staticmethod
    def trend_data(records):
        """
        Converts database rows into graph-ready
        data structures.

        Returns:
            {
                "dates": [],
                "sentiment": [],
                "risk": [],
                "sureness": []
            }
        """

        ticker_series = {}
        for record in records:
            ticker = record["ticker"]
            if ticker not in ticker_series:
                ticker_series[ticker] = {
                    "dates": [],
                    "sentiment": [],
                    "risk": [],
                    "sureness": []
                }

            ticker_series[ticker]["dates"].append(record["analysis_date"])
            ticker_series[ticker]["sentiment"].append(record["sentiment_score"])
            ticker_series[ticker]["risk"].append(record["risk_score"])
            ticker_series[ticker]["sureness"].append(record["sureness_score"])

        return {

            "dates": [

                record["analysis_date"]

                for record in records

            ],

            "sentiment": [

                record["sentiment_score"]

                for record in records

            ],

            "risk": [

                record["risk_score"]

                for record in records

            ],

            "sureness": [

                record["sureness_score"]

                for record in records

            ],

            # Keep each company as a separate series. This prevents a graph
            # from incorrectly drawing a line between different companies.
            "ticker_series": ticker_series

        }
