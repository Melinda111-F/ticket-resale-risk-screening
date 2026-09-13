"""Summarize and visualize ticket-risk screening results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def analyze(report_path: str | Path, output_directory: str | Path) -> dict[str, object]:
    """Create aggregate metrics, a JSON summary, and a distribution chart."""
    report = pd.read_csv(report_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    counts = report["risk_level"].value_counts().reindex(
        ["Low", "Medium", "High"], fill_value=0
    )
    predicted = report["risk_level"].eq("High")
    actual = report["label_is_risky"].astype(str).str.lower().eq("true")
    true_positive = int((predicted & actual).sum())
    false_positive = int((predicted & ~actual).sum())
    false_negative = int((~predicted & actual).sum())
    precision = true_positive / (true_positive + false_positive) if predicted.any() else 0.0
    recall = true_positive / (true_positive + false_negative) if actual.any() else 0.0

    summary = {
        "records_analyzed": int(len(report)),
        "risk_distribution": {level: int(counts[level]) for level in counts.index},
        "average_risk_score": round(float(report["risk_score"].mean()), 2),
        "high_risk_rate": round(float(predicted.mean()), 4),
        "synthetic_label_precision": round(precision, 4),
        "synthetic_label_recall": round(recall, 4),
    }
    (output_directory / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    colors = ["#2E8B57", "#E6A23C", "#C0392B"]
    figure, axis = plt.subplots(figsize=(7, 4.5))
    counts.plot(kind="bar", ax=axis, color=colors)
    axis.set_title("Ticket Resale Listing Risk Distribution")
    axis.set_xlabel("Risk level")
    axis.set_ylabel("Number of listings")
    axis.tick_params(axis="x", rotation=0)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_directory / "risk_distribution.png", dpi=180)
    plt.close(figure)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_csv")
    parser.add_argument("output_directory")
    args = parser.parse_args()
    print(json.dumps(analyze(args.report_csv, args.output_directory), indent=2))


if __name__ == "__main__":
    main()

