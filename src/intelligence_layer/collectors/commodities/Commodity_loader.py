
"""
Responsible for loading and validating the commodities YAML
configuration file. This module has exactly one responsibility:
read config, validate its structure, and return it in a parsed
form. It does not know that Yahoo Finance exists, does not make
network calls, and contains no collector or business logic."""
from pathlib import Path
from typing import Any

import yaml

from intelligence_layer.utils.exceptions import CollectorParseError
from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_TOP_LEVEL_KEYS = ("commodities", "settings")
REQUIRED_SETTINGS_KEYS = ("interval", "period")
REQUIRED_INSTRUMENT_KEYS = ("symbol", "name")

def load_commodity_config(yaml_path: str) -> dict[str, Any]:
    """
    Load and validate the commodities YAML configuration file.

    Reads the file at `yaml_path`, parses it with `yaml.safe_load`,
    and validates that it matches the expected structure:

        commodities:
            <category>:
                - symbol: str
                  name: str
        settings:
            interval: str
            period: str

    The set of categories under `commodities` (e.g. "energy",
    "metals") is intentionally not fixed, so new categories can be
    added to the YAML without requiring any code change here.

    Args:
        yaml_path: Path to the commodities YAML configuration file.

    Returns:
        A dictionary with the parsed and validated configuration,
        shaped as:
            {
                "commodities": {
                    "energy": [{"symbol": "CL=F", "name": "WTI Crude Oil"}, ...],
                    "metals": [{"symbol": "GC=F", "name": "Gold"}, ...],
                    ...
                },
                "settings": {"interval": "1d", "period": "5d"}
            }

    Raises:
        CollectorParseError: If the file is missing, is not valid
            YAML, or does not match the expected structure.
    """
    raw = _read_yaml_file(yaml_path)
    _validate_top_level_structure(raw, yaml_path)
    _validate_commodities_section(raw["commodities"], yaml_path)
    _validate_settings_section(raw["settings"], yaml_path)

    total_instruments = sum(len(v) for v in raw["commodities"].values())
    logger.info(
        f"Loaded commodity config from '{yaml_path}': "
        f"{len(raw['commodities'])} categories, "
        f"{total_instruments} instruments"
    )

    return raw


def _read_yaml_file(yaml_path: str) -> dict[str, Any]:
    """
    Read and safely parse a YAML file from disk.

    Args:
        yaml_path: Path to the YAML file.

    Returns:
        The parsed YAML content as a dictionary.

    Raises:
        CollectorParseError: If the file does not exist, cannot be
            read, or is not valid YAML.
    """
    path = Path(yaml_path)

    if not path.is_file():
        raise CollectorParseError(
            f"Commodity config file not found: '{yaml_path}'"
        )

    try:
        with path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CollectorParseError(
            f"Failed to parse commodity config '{yaml_path}': {e}"
        ) from e

    if not isinstance(content, dict):
        raise CollectorParseError(
            f"Commodity config '{yaml_path}' must contain a mapping "
            f"at the top level, got {type(content).__name__}"
        )

    return content


def _validate_top_level_structure(raw: dict[str, Any], yaml_path: str) -> None:
    """
    Validate that the top-level required keys are present.

    Args:
        raw: The parsed YAML content.
        yaml_path: Path to the source file, used for error messages.

    Raises:
        CollectorParseError: If a required top-level key is missing.
    """
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in raw]
    if missing:
        raise CollectorParseError(
            f"Commodity config '{yaml_path}' is missing required "
            f"top-level key(s): {missing}"
        )


def _validate_commodities_section(
    commodities: Any, yaml_path: str
) -> None:
    """
    Validate the `commodities` section structure.

    Ensures `commodities` is a mapping of category name to a list of
    instruments, and that each instrument contains the required
    keys. Category names themselves are not restricted, so new
    categories can be added freely.

    Args:
        commodities: The value under the `commodities` key.
        yaml_path: Path to the source file, used for error messages.

    Raises:
        CollectorParseError: If the section or any instrument within
            it does not match the expected structure.
    """
    if not isinstance(commodities, dict) or not commodities:
        raise CollectorParseError(
            f"'commodities' section in '{yaml_path}' must be a "
            f"non-empty mapping of category to instrument list"
        )

    for category, instruments in commodities.items():
        if not isinstance(instruments, list) or not instruments:
            raise CollectorParseError(
                f"Category '{category}' in '{yaml_path}' must be a "
                f"non-empty list of instruments"
            )

        for index, instrument in enumerate(instruments):
            if not isinstance(instrument, dict):
                raise CollectorParseError(
                    f"Instrument at index {index} in category "
                    f"'{category}' in '{yaml_path}' must be a mapping"
                )

            missing = [
                key for key in REQUIRED_INSTRUMENT_KEYS
                if key not in instrument
            ]
            if missing:
                raise CollectorParseError(
                    f"Instrument at index {index} in category "
                    f"'{category}' in '{yaml_path}' is missing "
                    f"required key(s): {missing}"
                )


def _validate_settings_section(settings: Any, yaml_path: str) -> None:
    """
    Validate the `settings` section structure.

    Args:
        settings: The value under the `settings` key.
        yaml_path: Path to the source file, used for error messages.

    Raises:
        CollectorParseError: If the section is missing required keys.
    """
    if not isinstance(settings, dict):
        raise CollectorParseError(
            f"'settings' section in '{yaml_path}' must be a mapping"
        )

    missing = [key for key in REQUIRED_SETTINGS_KEYS if key not in settings]
    if missing:
        raise CollectorParseError(
            f"'settings' section in '{yaml_path}' is missing "
            f"required key(s): {missing}"
        )


