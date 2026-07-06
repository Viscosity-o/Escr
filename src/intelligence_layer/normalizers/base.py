"""
normalizers/base.py
===================
Defines the abstract base interface for all normalizers.
"""
from abc import ABC, abstractmethod
from typing import Any

from intelligence_layer.models.intelligence_record import IntelligenceRecord


class BaseNormalizer(ABC):
    """
    Abstract base class for all data normalizers.

    Each normalizer maps the raw data from one specific source
    into the shared IntelligenceRecord schema.
    """

    @abstractmethod
    def normalize(self, raw_data: Any) -> list[IntelligenceRecord]:
        """
        Transform raw (validated) data into one or more IntelligenceRecords.

        A single raw payload may produce multiple records
        (e.g., a news feed response containing many articles).

        Args:
            raw_data: Validated raw data from a collector.

        Returns:
            A list of normalized IntelligenceRecord objects.
        """
        ...
