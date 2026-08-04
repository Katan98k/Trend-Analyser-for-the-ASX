"""
---------------------------------------------------------
Trend Analyzer for the ASX
Trend Graph Generator

Transforms saved article scores into dark-theme Matplotlib
comparison charts for sentiment, risk, and sureness trends.

Author: Karan Attavar
---------------------------------------------------------
"""

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
    METRIC_PALETTES = {
        "sentiment": ("#18e58d", "#42f5a7", "#36c7ff", "#7affd0", "#66a7ff"),
        "risk": ("#ff405c", "#ff7186", "#ff9f43", "#ff6b3d", "#f45bca"),
        "sureness": ("#ffc928", "#ffe267", "#a98cff", "#ffae35", "#62d9ff")
    }

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

    def generate_comparison_graph(self, ticker_series, metric, filename, title, ylabel):
        """Plot neon market signals on the dark visual system used by the UI."""
        if plt is None:
            return ""

        figure, axis = plt.subplots(figsize=(10.5, 5.7), facecolor=self.BACKGROUND)
        axis.set_facecolor(self.PANEL)
        palette = self.METRIC_PALETTES.get(metric, self.METRIC_PALETTES["sentiment"])

        date_axis_is_datetime = True
        for index, (ticker, series) in enumerate(ticker_series.items()):
            dates = self._dates(series["dates"])
            values = series[metric]
            color = palette[index % len(palette)]
            date_axis_is_datetime = date_axis_is_datetime and all(isinstance(value, datetime) for value in dates)

            # Layered strokes create the restrained neon bloom shown in the mock-ups.
            axis.plot(dates, values, color=color, linewidth=8, alpha=0.035, solid_capstyle="round")
            axis.plot(dates, values, color=color, linewidth=5, alpha=0.07, solid_capstyle="round")
            axis.plot(
                dates,
                values,
                color=color,
                marker="o",
                markersize=5.5,
                markerfacecolor=color,
                markeredgecolor=self.PANEL,
                markeredgewidth=1.4,
                linewidth=2.35,
                solid_capstyle="round",
                label=ticker,
                zorder=4
            )
            if len(dates) > 1:
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
        return {
            "sentiment": self.generate_comparison_graph(
                series, "sentiment", "sentiment.png",
                "Sentiment Comparison by Company", "Sentiment Score (0-100)"
            ),
            "risk": self.generate_comparison_graph(
                series, "risk", "risk.png",
                "Risk Comparison by Company", "Risk Score (0-100)"
            ),
            "sureness": self.generate_comparison_graph(
                series, "sureness", "sureness.png",
                "Prediction Sureness by Company", "Sureness Score (0-100)"
            )
        }
