"""
Plot blockchain RPC provider domain ranks and estimated traffic shares.
"""

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def plot_domains(input_path, output_dir):
    """Create individual plots and a combined plot for the most popular domains.
    :param input_path: the aggregated provider CSV file to read
    :param output_dir: the directory in which to save plots
    :returns: the number of processed domains
    """
    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or "domain" not in reader.fieldnames:
            raise ValueError("Input CSV must contain a 'domain' column.")
        periods = sorted(
            (field for field in reader.fieldnames if field not in {"domain", "provider"}),
            key=lambda period: datetime.strptime(period, "%Y-%m-%d"), # Parse date columns so sorting is chronological
        )
        rows = list(reader)

    output_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        ranks = [(period, int(row[period].rstrip("+"))) for period in periods if row.get(period, "").strip()] # Tranco marks ranks beyond its list with "+".
        if not ranks:
            continue

        labels = [datetime.strptime(period, "%Y-%m-%d").strftime("%d\n%b\n%Y") for period, _ in ranks]
        values = [value for _, value in ranks]
        figure, axis = plt.subplots(figsize=(10, 5.5))
        axis.plot(labels, values, marker="o", linewidth=2)
        axis.invert_yaxis()
        axis.yaxis.set_major_formatter(
            FuncFormatter(
                lambda value, _: "1,000,000+" if value >= 1_000_000 else f"{value:,.0f}" # Display the missing-rank marker at the maximum rank value.
            )
        )
        axis.set_title(f"{row['domain']} ({row['provider']})")
        axis.set_ylabel("Rank (higher means more popular)")
        axis.grid(True, alpha=0.3)
        figure.tight_layout()
        # Replace characters that can't be in a filename.
        filename = re.sub(r"[^A-Za-z0-9._-]+", "_", row["domain"])
        figure.savefig(output_dir / f"{filename}.png", dpi=150)
        plt.close(figure)

    ranked_rows = []
    for row in rows:
        values = [int(row[period].rstrip("+")) for period in periods if row.get(period, "").strip()]
        if values:
            ranked_rows.append((sum(values) / len(values), row))

    top_rows = [row for _, row in sorted(ranked_rows)[:5]]
    labels = [datetime.strptime(period, "%Y-%m-%d").strftime("%d\n%b\n%Y") for period in periods]
    figure, axis = plt.subplots(figsize=(12, 7))
    for row in top_rows:
        values = [int(row[period].rstrip("+")) if row.get(period, "").strip() else None for period in periods]
        axis.plot(labels, values, marker="o", linewidth=2, label=row["domain"])
    axis.invert_yaxis()
    axis.yaxis.set_major_formatter(
        FuncFormatter(
            lambda value, _: "1,000,000+" if value >= 1_000_000 else f"{value:,.0f}"
        )
    )
    axis.set_title("Top 5 Domains by Average Tranco Rank")
    axis.set_ylabel("Rank (higher means more popular)")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    figure.tight_layout()
    figure.savefig(output_dir / "top_5_domains.png", dpi=150, bbox_inches="tight")
    plt.close(figure)

    return len(rows)


def plot_provider_traffic(input_path, output_path):
    """Create a stacked provider-share area chart over the traffic dates."""
    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or "provider" not in reader.fieldnames:
            raise ValueError("Traffic CSV must contain a 'provider' column.")
        # Parse date columns so sorting is chronological.
        periods = sorted(
            (field for field in reader.fieldnames if field != "provider"),
            key=lambda period: datetime.strptime(period, "%Y-%m-%d"),
        )
        rows = list(reader)

    ranked_providers = sorted(
        rows,
        key=lambda row: sum(float(row.get(period, 0) or 0) for period in periods),
        reverse=True,
    )
    providers = ranked_providers[:10]
    other_rows = ranked_providers[10:]
    if other_rows:
        providers.append(
            {
                "provider": "Others",
                **{
                    period: sum(float(row.get(period, 0) or 0) for row in other_rows)
                    for period in periods
                },
            }
        )
    labels = [datetime.strptime(period, "%Y-%m-%d").strftime("%d\n%b\n%Y") for period in periods]
    figure, axis = plt.subplots(figsize=(max(12, len(periods) * 0.8), 8))
    colour_map = plt.get_cmap("tab20").resampled(max(len(providers), 1))
    x_values = list(range(len(periods)))
    provider_values = [[float(row.get(period, 0) or 0) for period in periods] for row in providers]
    axis.stackplot(
        x_values,
        *provider_values,
        labels=[row["provider"] for row in providers],
        colors=[colour_map(index) for index in range(len(providers))],
    )
    axis.set_xticks(x_values, labels)

    axis.set_title("Estimated RPC Provider Traffic Share by Tranco Date")
    axis.set_ylabel("Estimated traffic share (%)")
    axis.set_ylim(0, 100)
    axis.grid(axis="y", alpha=0.3)
    axis.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize="small")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default="ranking.csv",
        help="Aggregated provider CSV path",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="domain_plots",
        help="Directory for generated PNG plots",
    )
    parser.add_argument(
        "--traffic",
        default="traffic_share.csv",
        help="Provider traffic-share CSV for the stacked area chart",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    count = plot_domains(Path(args.input), output_dir)
    traffic_path = Path(args.traffic)
    if traffic_path.is_file():
        plot_provider_traffic(traffic_path, output_dir / "traffic_area_chart.png")
    print(f"Created plots for {count} domains in {args.output}.")


if __name__ == "__main__":
    main()
