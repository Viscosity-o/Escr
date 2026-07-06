"""
utils/config_loader.py
======================
Loads and exposes application configuration from environment variables
and YAML config files.

This utility is the single access point for all configuration values,
ensuring nothing else in the codebase reaches directly into os.environ.
"""
import os
from pathlib import Path


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """
    Read an environment variable by key.

    Args:
        key:      The environment variable name.
        default:  Fallback value if not set.
        required: If True, raises EnvironmentError when the key is missing.

    Returns:
        The value of the environment variable, or the default.

    Raises:
        EnvironmentError: If required=True and the key is not set.
    """
    value = os.environ.get(key, default)
    if required and value is None:
        raise OSError(f"Required environment variable '{key}' is not set.")
    return value


def get_config_path(filename: str) -> Path:
    """
    Resolve the path to a file in the project's config/ directory.

    Args:
        filename: Name of the config file (e.g., "sources.yaml").

    Returns:
        Absolute Path object pointing to config/<filename>.
    """
    root = Path(__file__).resolve().parents[3]  # project root
    return root / "config" / filename
