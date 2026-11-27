"""
Compute decentralisation metrics for RPC provider traffic.
"""

import argparse
import csv
from pathlib import Path

from helper import get_metrics_client_api
from metrics.concentration_ratio import compute_concentration_ratio
from metrics.entropy import compute_entropy
from metrics.herfindahl_hirschman_index import compute_hhi
from metrics.nakamoto_coefficient import compute_nakamoto_coefficient
from metrics.total_entities import compute_total_entities

# Each entry pairs a metric function with whether it requires a parameter.
METRICS = {
    "hhi": (compute_hhi, False),
    "nakamoto_coefficient": (compute_nakamoto_coefficient, False),
    "total_entities": (compute_total_entities, False),
    "entropy": (compute_entropy, True),
    "concentration_ratio": (compute_concentration_ratio, True),
}


def calculate_distribution_metrics(distribution, metric_tokens):
    """Calculate the requested metrics for one period's provider distribution."""
    results = {}
    for token in metric_tokens:
        metric, separator, raw_parameter = token.partition("=")
        if metric not in METRICS or bool(separator) != METRICS[metric][1]:
            raise ValueError(f"Unsupported metric token: '{token}'.")
        function, has_parameter = METRICS[metric]
        if has_parameter:
            try:
                parameter = float(raw_parameter)
            except ValueError as error:
                raise ValueError(f"Invalid parameter in metric token: '{token}'.") from error
            if parameter.is_integer():
                parameter = int(parameter)
            if metric == "concentration_ratio" and (not isinstance(parameter, int) or parameter < 1):
                raise ValueError("Concentration ratio parameters must be positive integers.")
            results[token] = function(distribution, parameter)
        else:
            results[token] = function(distribution)

    return results


def compute_provider_metrics(input_path, output_path):
    """Compute metrics for every traffic-share period and write CSV output."""
    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or "provider" not in reader.fieldnames:
            raise ValueError("Input CSV must contain a 'provider' column.")
        periods = [field for field in reader.fieldnames if field != "provider"]
        rows = list(reader)

    metrics_by_period = []
    metric_tokens = get_metrics_client_api()
    for period in periods:
        distribution = sorted((float(row[period]) for row in rows if row.get(period, "").strip()), reverse=True)
        metrics_by_period.append({"date": period, **calculate_distribution_metrics(distribution, metric_tokens)})

    metric_names = list(metrics_by_period[0]) if metrics_by_period else ["date"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=metric_names)
        writer.writeheader()
        writer.writerows(metrics_by_period)

    return len(metrics_by_period)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default="traffic_share.csv",
        help="Provider traffic-share CSV path",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="metrics/metrics.csv",
        help="CSV path for computed metrics",
    )
    args = parser.parse_args()

    count = compute_provider_metrics(Path(args.input), Path(args.output))
    print(f"Computed metrics for {count} periods; wrote {args.output}.")


if __name__ == "__main__":
    main()
