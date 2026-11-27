"""
Download Tranco lists, then extract blockchain RPC provider domains.
"""

import argparse
import csv
import io
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

MISSING_RANK = "1000000+"
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
LIST_DIRECTORY = Path(__file__).parent / "tranco_lists"


def download_latest_list(output_directory=LIST_DIRECTORY):
	"""Download the latest Tranco list into the snapshot directory."""
	request = urllib.request.Request(TRANCO_URL, headers={"User-Agent": "client-api-pipeline/1.0"})
	with urllib.request.urlopen(request, timeout=120) as response:
		archive = response.read()

	list_date = datetime.now(timezone.utc)

	output_directory.mkdir(parents=True, exist_ok=True)
	output_path = output_directory / list_date.strftime("%Y-%m-%d.csv")

	with zipfile.ZipFile(io.BytesIO(archive)) as compressed:
		csv_names = [name for name in compressed.namelist() if name.endswith(".csv")]
		if len(csv_names) != 1:
			raise ValueError("Tranco archive did not contain exactly one CSV file.")
		raw_csv = compressed.read(csv_names[0])

	if not raw_csv:
		raise ValueError("Downloaded Tranco CSV is empty.")

	output_path.write_bytes(raw_csv)
	print(f"Downloaded latest Tranco list to {output_path}.")
	return output_path


def load_provider_domains():
	"""Load provider domain mappings from the CSV file.
	:returns: provider names mapped to their registered domains
	"""
	provider_domains = {}
	provider_path = Path(__file__).parent / "provider_domains.csv"
	with provider_path.open("r", encoding="utf-8", newline="") as csv_file:
		for row in csv.DictReader(csv_file):
			provider_domains.setdefault(row["provider"], []).append(row["domain"])
	return provider_domains


PROVIDER_DOMAINS = load_provider_domains()
DOMAIN_PROVIDERS = {}
for provider, domains in PROVIDER_DOMAINS.items():
	for domain in domains:
		DOMAIN_PROVIDERS.setdefault(domain, provider)


def normalise_domain(value):
	"""Return a comparable hostname without URL syntax or a trailing dot.
	:param value: the domain or URL to normalise
	:returns: the normalised hostname
	"""
	domain = value.strip().lower().rstrip(".")
	if "://" in domain:
		domain = domain.split("://", 1)[1]
	return domain.split("/", 1)[0].split(":", 1)[0]


def find_provider(domain):
	"""Return the provider owning the domain, or None when it is not registered.
	:param domain: the domain to match against registered providers
	:returns: the provider name, or None when no provider matches
	"""
	normalised = normalise_domain(domain)
	labels = normalised.split(".")
	for index in range(len(labels)):
		provider = DOMAIN_PROVIDERS.get(".".join(labels[index:]))
		if provider is not None:
			return provider
	return None


def extract_providers(input_path):
	"""Read a Tranco CSV and return matching rows.
	:param input_path: the Tranco CSV file to read
	:returns: matching domain rows with their ranks and provider names
	"""
	matches = []
	with input_path.open("r", encoding="utf-8", newline="") as csv_file:
		reader = csv.reader(csv_file)
		for row_number, row in enumerate(reader, start=1):
			if len(row) < 2:
				continue
			rank, domain = row[0].strip(), normalise_domain(row[1])
			if row_number == 1 and rank.lower() in {"rank", "ranking"}:
				continue
			provider = find_provider(domain)
			if provider is not None:
				matches.append({"rank": rank, "domain": domain, "provider": provider})
	return matches


def write_matches(matches, output_path):
	"""Write combined provider matches to a CSV file.
	:param matches: the provider rows to write
	:param output_path: the CSV file to create
	:returns: None
	"""
	fieldnames = tuple(matches[0]) if matches else ("domain", "provider")
	with output_path.open("w", encoding="utf-8", newline="") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(matches)


def combine_matches(input_paths):
	"""Combine matches into one row per domain with a rank per input list.
	:param input_paths: the Tranco CSV files to combine
	:returns: combined provider rows with one rank column per input list
	"""
	periods = [input_path.stem for input_path in input_paths]
	combined = {}
	for input_path, period in zip(input_paths, periods):
		for match in extract_providers(input_path):
			row = combined.setdefault(
				match["domain"],
				{"domain": match["domain"], "provider": match["provider"]},
			)
			row[period] = match["rank"]
	return [
		{"domain": row["domain"], "provider": row["provider"], **{
			period: row.get(period, MISSING_RANK) for period in periods
		}}
		for row in combined.values()
	]


def resolve_inputs(input_arguments):
	"""Resolve explicit CSV arguments or discover every CSV in tranco_lists.
	:param input_arguments: CSV paths or directories supplied on the command line
	:returns: the CSV paths to process
	"""
	if not input_arguments:
		input_paths = sorted((Path(__file__).parent / "tranco_lists").glob("*.csv"))
	else:
		input_paths = []
		for input_argument in input_arguments:
			input_path = Path(input_argument)
			if input_path.is_dir():
				input_paths.extend(sorted(input_path.glob("*.csv")))
			else:
				input_paths.append(input_path)
	if not input_paths:
		raise FileNotFoundError("No Tranco CSV files found in tranco_lists.")
	missing_paths = [path for path in input_paths if not path.is_file()]
	if missing_paths:
		raise FileNotFoundError(f"Input CSV does not exist: {missing_paths[0]}")
	return input_paths


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"input",
		nargs="*",
		help="Tranco CSV paths or a directory (defaults to all CSVs in tranco_lists)",
	)
	parser.add_argument("-o", "--output", default="ranking.csv")
	args = parser.parse_args()

	download_latest_list()
	input_paths = resolve_inputs(args.input)
	matches = combine_matches(input_paths)
	write_matches(matches, Path(args.output))
	print(f"Found {len(matches)} matching domains in {len(input_paths)} input file(s); wrote {args.output}.")


if __name__ == "__main__":
	main()
