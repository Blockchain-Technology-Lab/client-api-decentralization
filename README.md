# Client API decentralisation

This project estimates decentralisation among blockchain RPC providers. It uses Tranco domain rankings to estimate provider traffic shares, calculates decentralisation metrics, and generates plots.

To run the recurring pipeline:

```bash
./automation_client_api.sh
```

The script runs the pipeline immediately and repeats it every 30 days. It uses Bash and expects a Python virtual environment at `venv/`. Create and populate it before running:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

The pipeline downloads Tranco lists, so it requires an internet connection. Provider domain mappings are maintained in `provider_domains.csv`, and the metrics to calculate are configured in `config.yaml`.

---

## Workflow Overview

1. **Tranco data collection:** `tranco_crawler.py` downloads a Tranco snapshot and matches its domains against the provider mappings.
2. **Traffic estimation:** `compute_traffic.py` applies Zipf's law to domain ranks and aggregates the estimates by provider.
3. **Metrics computation:** `compute_metrics.py` calculates the configured metrics for each snapshot date.
4. **Visualisation:** `plot.py` creates domain-rank charts and a provider traffic-share chart.
5. **Archiving:** `automation_client_api.sh` moves each run's CSVs and plots to `output/YYYY-MM-DD/`.

---

## Script Descriptions

### Core Scripts

- **`tranco_crawler.py`**  
  Downloads the latest Tranco list, matches domains using `provider_domains.csv`, and writes provider rankings to `ranking.csv`. It can also be given CSV files or directories as inputs.

- **`compute_traffic.py`**  
  Reads `ranking.csv` and writes estimated provider traffic shares to `traffic_share.csv`. The Zipf exponent can be changed with `--exponent`.

- **`compute_metrics.py`**  
  Reads provider traffic shares and writes metrics for each date to `metrics/metrics.csv`.

- **`plot.py`**  
  Creates individual domain-rank plots, a plot of the five domains with the best average Tranco rank, and—when a traffic-share CSV is available—a stacked provider traffic-share chart.

- **`helper.py`**  
  Loads and validates the metric configuration from `config.yaml`.

### Metrics

The `metrics/` package implements:

- **`herfindahl_hirschman_index.py`** — Herfindahl-Hirschman Index (HHI).
- **`nakamoto_coefficient.py`** — Nakamoto coefficient, using the tau index.
- **`entropy.py`** — Entropy metrics.
- **`concentration_ratio.py`** — Top-*n* concentration ratios.
- **`total_entities.py`** — Number of providers with positive traffic.
- **`tau_index.py`** — Shared calculation used by the Nakamoto coefficient.

### Automation and Configuration

- **`automation_client_api.sh`**  
  Runs the crawler, traffic estimation, metrics, and plotting scripts, then archives the results. It loops every 30 days until stopped.

- **`config.yaml`**  
  Defines the metrics to calculate.

- **`provider_domains.csv`**  
  Maps provider names to the domains used to identify them in Tranco lists.

- **`requirements.txt`**  
  Lists the Python dependencies.

---

## Output

The pipeline produces:

- `ranking.csv` — provider domains and their ranks by Tranco snapshot.
- `traffic_share.csv` — estimated traffic shares by provider and date.
- `metrics/metrics.csv` — configured decentralisation metrics by date.
- PNG plots in `domain_plots/`.

The automation script archives these under `output/YYYY-MM-DD/`, with domain plots in the `plots/` subdirectory.

---

## Directory Structure

```text
client-api-decentralization/
├── automation_client_api.sh
├── compute_metrics.py
├── compute_traffic.py
├── helper.py
├── plot.py
├── tranco_crawler.py
├── config.yaml
├── provider_domains.csv
├── requirements.txt
├── metrics/
│   ├── concentration_ratio.py
│   ├── entropy.py
│   ├── herfindahl_hirschman_index.py
│   ├── nakamoto_coefficient.py
│   ├── tau_index.py
│   └── total_entities.py
├── tranco_lists/
└── output/
```
