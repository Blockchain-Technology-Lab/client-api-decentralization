"""
Estimate RPC provider web traffic from Tranco ranks using Zipf's law.

The estimate assigns each domain a weight of ``1 / rank**exponent`` and
normalises the weights within each Tranco snapshot. Domain shares are then
summed by provider.
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

MISSING_RANK = 1_000_000
DEFAULT_EXPONENT = 1.0


def compute_traffic(input_path, output_path, exponent=DEFAULT_EXPONENT):
    """Write normalised Zipf traffic shares aggregated by provider."""
    if exponent <= 0:
        raise ValueError("Zipf exponent must be greater than zero.")

    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or not {"provider", "domain"} <= set(reader.fieldnames):
            raise ValueError("Input CSV must contain 'domain' and 'provider' columns.")
        periods = sorted(
            (field for field in reader.fieldnames if field not in {"domain", "provider"}),
            key=lambda period: datetime.strptime(period, "%Y-%m-%d"), # Parse dates to keep snapshots in chronological order.
        )
        rows = list(reader)

    provider_shares = {}
    for period in periods:
        weights = [
            1 / int(row[period].strip().rstrip("+") or MISSING_RANK) ** exponent # Tranco appends "+" to ranks beyond its list; use the fallback rank.
            for row in rows
            if row.get(period, "").strip()
        ]
        total_weight = sum(weights)
        if total_weight == 0:
            raise ValueError(f"No usable ranks found for {period}.")

        for row in rows:
            rank = row.get(period, "").strip()
            if not rank:
                continue
            provider = row["provider"]
            shares = provider_shares.setdefault(provider, {})
            shares[period] = shares.get(period, 0.0) + (1 / int(rank.strip().rstrip("+") or MISSING_RANK) ** exponent) / total_weight * 100

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["provider", *periods]
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for provider in sorted(provider_shares):
            writer.writerow(
                {
                    "provider": provider,
                    **{
                        period: f"{provider_shares[provider].get(period, 0.0):.10f}"
                        for period in periods
                    },
                }
            )

    return len(provider_shares)


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
        default="traffic_share.csv",
        help="CSV path for provider traffic-share estimates",
    )
    parser.add_argument(
        "--exponent",
        type=float,
        default=DEFAULT_EXPONENT,
        help="Zipf exponent (default: 1)",
    )
    args = parser.parse_args()

    count = compute_traffic(Path(args.input), Path(args.output), args.exponent)
    print(
        f"Computed traffic shares for {count} providers using Zipf exponent "
        f"{args.exponent:g}; wrote {args.output}."
    )


if __name__ == "__main__":
    main()
