#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" # makes the script run from its own directory, regardless of where it is launched

source venv/bin/activate # venv is the Python virtual environment where all dependencies must be installed

while true
do
    python3 tranco_crawler.py
    python3 compute_traffic.py
    python3 compute_metrics.py
    python3 plot.py

    RUN_DATE="$(date +%Y-%m-%d)"
    RUN_OUTPUT="output/$RUN_DATE"
    mkdir -p "$RUN_OUTPUT/plots"

    mv ranking.csv traffic_share.csv "$RUN_OUTPUT/"
    mv metrics/*.csv "$RUN_OUTPUT/"
    mv domain_plots/traffic_area_chart.png "$RUN_OUTPUT/"
    mv domain_plots/*.png "$RUN_OUTPUT/plots/"

    sleep 30d
done
