"""
Helpers for loading configuration.
"""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).with_name("config.yaml")


def get_config_data():
    """Load configuration data from the config file."""
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, dict):
        raise ValueError("Metrics config must be a YAML mapping.")
    return config


def _expand_metric_config(metric_config):
    """Expand metric names and parameter mappings into metric tokens."""
    if isinstance(metric_config, list):
        if not all(isinstance(metric, str) and metric.strip() for metric in metric_config):
            raise ValueError("Client API metrics must be non-empty strings.")
        tokens = metric_config
    elif isinstance(metric_config, dict):
        tokens = []
        for metric, parameters in metric_config.items():
            if not isinstance(metric, str) or not metric.strip():
                raise ValueError("Metric names in config must be non-empty strings.")
            if parameters is None:
                tokens.append(metric)
                continue
            if not isinstance(parameters, list) or not all(
                isinstance(parameter, (int, float))
                and not isinstance(parameter, bool)
                for parameter in parameters
            ):
                raise ValueError(
                    f"Parameters for metric '{metric}' must be numeric lists."
                )
            tokens.extend(f"{metric}={parameter}" for parameter in parameters)
    else:
        raise ValueError("'client_api_metrics' must be a list or mapping.")

    if len(tokens) != len(set(tokens)):
        raise ValueError("Client API metric tokens must be unique.")
    return tokens


def get_metrics_client_api():
    """
    Retrieve metric tokens to compute for client API analysis.

    Supports a list such as ``['hhi', 'nakamoto_coefficient']`` or a mapping
    such as ``{'concentration_ratio': [1, 3]}``.
    """
    return _expand_metric_config(get_config_data().get("client_api_metrics"))
