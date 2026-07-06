"""
collectors/base.py
==================
Defines the abstract base interface that every collector must implement.

All collectors share the same contract regardless of the data source,
making them interchangeable and easy to test in isolation.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """
    Abstract base class for all data source collectors.

    Every concrete collector must implement `collect()` which fetches
    raw data from its source and returns it as a plain Python object
    (dict, list, str, bytes, etc.) — no transformation applied.
    """

    @abstractmethod
    def collect(self) -> Any:
        """
        Fetch raw data from the external source.

        Returns:
            Raw data in whatever native format the source provides.

        Raises:
            CollectorConnectionError: If the source cannot be reached.
            CollectorParseError: If the response cannot be read.
        """
        ...

    @property
    @abstractmethod
    def source_id(self) -> str:
        """
        A unique, stable identifier for this data source.
        Used for logging, routing, and traceability.

        Example: "reuters_news", "vessel_finder_ais", "ofac_sanctions"
        """
        ...
