"""
models/source_config.py
========================
Represents the configuration contract for a data source.

This model is used to describe and pass configuration into collectors
in a structured, type-safe way — decoupled from any config file format.
"""
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """
    Configuration descriptor for a single external data source.

    Attributes:
        source_id:       Unique identifier matching the collector's source_id.
        enabled:         Whether this source should be actively collected.
        poll_interval_seconds: How frequently to collect from this source.
        timeout_seconds: Max wait time per collection attempt.
        max_retries:     Number of retry attempts on transient failures.
        extra:           Arbitrary additional config (URLs, keys, options).
                         Values are read at runtime from environment variables.
    """

    source_id: str
    enabled: bool = True
    poll_interval_seconds: int = 300  # 5 minutes default
    timeout_seconds: int = 30
    max_retries: int = 3
    extra: dict[str, str] = field(default_factory=dict)
