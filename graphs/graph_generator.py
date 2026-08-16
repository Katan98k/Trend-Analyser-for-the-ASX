"""
---------------------------------------------------------
Trend Analyzer for the ASX
Trend Graph Generator

Transforms saved article scores into dark-theme Matplotlib
comparison charts for sentiment, risk, and sureness trends.

Author: Karan Attavar
---------------------------------------------------------
"""

import colorsys
import os
from datetime import datetime

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:  # pragma: no cover - optional dependency
    plt = None
    mdates = None

from config import Config


class GraphGenerator:
    """Generate one comparison line per ticker for each analysis metric."""

    BACKGROUND = "#0b0e13"
    PANEL = "#10141a"
    GRID = "#29313b"
    TEXT = "#f3f6fa"
    MUTED = "#8590a0"
    MARKERS = ("o", "s", "^", "D", "P", "X", "v", "<", ">", "h", "p", "*")
    LINE_STYLES = ("-", "--", "-.", ":")

    def __init__(self):
        """Create the configured graph output directory when required."""
        self.output_folder = Config.GRAPH_FOLDER
        os.makedirs(self.output_folder, exist_ok=True)

    @staticmethod
    def _dates(date_strings):
        """Convert database timestamps to date values Matplotlib can format."""
        parsed_dates = []
        for value in date_strings:
            try:
                parsed_dates.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
            except ValueError:
                try:
                    parsed_dates.append(datetime.strptime(value, "%Y-%m-%d %H:%M:%S"))
                except ValueError:
                    parsed_dates.append(value)
        return parsed_dates

    @classmethod
    def _ticker_styles(cls, tickers):
        """Assign every displayed ticker a distinct, reusable visual style.

        Colours are generated across the full hue wheel for the current ticker
        set rather than taken from a fixed palette. This prevents palette
        cycling when the user adds more companies. Sorting also guarantees that
        the same ticker receives the same colour in all three graphs generated
        for a request.
        """
        ordered_tickers = sorted(set(tickers), key=str.casefold)
        ticker_count = max(len(ordered_tickers), 1)
        styles = {}

        for index, ticker in enumerate(ordered_tickers):
            # Start in cyan, then distribute the remaining tickers evenly over
            # the hue wheel. HLS keeps every colour bright on the dark panel.
            hue = (0.52 + (index / ticker_count)) % 1.0
            color = colorsys.hls_to_rgb(hue, 0.62, 0.82)
            styles[ticker] = {
                "color": color,
                "marker": cls.MARKERS[index % len(cls.MARKERS)],
                "linestyle": cls.LINE_STYLES[index % len(cls.LINE_STYLES)],
            }

        return styles

    def generate_comparison_graph(
        self, ticker_series, metric, filename, title, ylabel, ticker_styles=None
    ):
        """Plot neon market signals on the dark visual system used by the UI."""
        if plt is None:
            return ""

        figure, axis = plt.subplots(figsize=(10.5, 5.7), facecolor=self.BACKGROUND)
        axis.set_facecolor(self.PANEL)
        ticker_styles = ticker_styles or self._ticker_styles(ticker_series)
        ordered_tickers = sorted(ticker_series, key=str.casefold)

        date_axis_is_datetime = True
        for index, ticker in enumerate(ordered_tickers):
            series = ticker_series[ticker]
            dates = self._dates(series["dates"])
            values = series[metric]
            style = ticker_styles[ticker]
            color = style["color"]
            date_axis_is_datetime = date_axis_is_datetime and all(isinstance(value, datetime) for value in dates)

            # Layered strokes create the restrained neon bloom shown in the mock-ups.
            axis.plot(
                dates, values, color=color, linewidth=8, alpha=0.035,
                linestyle=style["linestyle"], solid_capstyle="round"
            )
            axis.plot(
                dates, values, color=color, linewidth=5, alpha=0.07,
                linestyle=style["linestyle"], solid_capstyle="round"
            )
            axis.plot(
                dates,
                values,
                color=color,
                marker=style["marker"],
                markersize=5.5,
                markerfacecolor=color,
                markeredgecolor=self.PANEL,
                markeredgewidth=1.4,
                linewidth=2.35,
                linestyle=style["linestyle"],
                solid_capstyle="round",
                label=ticker,
                zorder=4 + index
            )
            if len(ordered_tickers) == 1 and len(dates) > 1:
                axis.fill_between(dates, values, 0, color=color, alpha=0.09, zorder=1)

        axis.set_title(title, loc="left", color=self.TEXT, fontsize=15, fontweight="bold", pad=18)
        axis.set_xlabel("News article publication date", color=self.MUTED, labelpad=12)
        axis.set_ylabel(ylabel, color=self.MUTED, labelpad=12)
        axis.set_ylim(0, 100)
        axis.set_axisbelow(True)
        axis.grid(axis="y", color=self.GRID, linewidth=0.8, alpha=0.72)
        axis.grid(axis="x", color=self.GRID, linewidth=0.5, alpha=0.24)
        axis.tick_params(axis="both", colors=self.MUTED, labelsize=8.5, length=0)
        axis.tick_params(axis="x", rotation=35, pad=8)

        for spine in axis.spines.values():
            spine.set_color("#252c35")
            spine.set_linewidth(0.8)

        if mdates is not None and date_axis_is_datetime:
            axis.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=7))
            axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

        if ticker_series:
            legend = axis.legend(
                title="ASX ticker",
                loc="best",
                frameon=True,
                facecolor="#151a21",
                edgecolor="#303844",
                labelcolor=self.TEXT,
                fontsize=8.5
            )
            legend.get_title().set_color(self.MUTED)

        figure.tight_layout(pad=1.6)
        output_path = os.path.join(self.output_folder, filename)
        figure.savefig(output_path, dpi=170, facecolor=self.BACKGROUND, bbox_inches="tight")
        plt.close(figure)
        return f"graphs/{filename}"

    def generate_all(self, trend_data):
        """Generate company-comparison charts for all three score types."""
        series = trend_data["ticker_series"]
        ticker_styles = self._ticker_styles(series)
        return {
            "sentiment": self.generate_comparison_graph(
                series, "sentiment", "sentiment.png",
                "Sentiment Comparison by Company", "Sentiment Score (0-100)",
                ticker_styles
            ),
            "risk": self.generate_comparison_graph(
                series, "risk", "risk.png",
                "Risk Comparison by Company", "Risk Score (0-100)",
                ticker_styles
            ),
            "sureness": self.generate_comparison_graph(
                series, "sureness", "sureness.png",
                "Prediction Sureness by Company", "Sureness Score (0-100)",
                ticker_styles
            )
        }
