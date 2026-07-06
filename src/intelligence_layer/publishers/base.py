"""
publishers/base.py
==================
Defines the abstract base interface for all publishers.
"""
from abc import ABC, abstractmethod

from intelligence_layer.models.intelligence_record import IntelligenceRecord


class BasePublisher(ABC):
    """
    Abstract base class for all downstream publishers.

    Decouples the rest of the module from the specific
    technology used to forward data (queue, HTTP, file, etc.).
    """

    @abstractmethod
    def publish(self, records: list[IntelligenceRecord]) -> None:
        """
        Forward a batch of normalized records to the downstream target.

        Args:
            records: One or more normalized IntelligenceRecord objects to publish.

        Raises:
            PublisherConnectionError: If the downstream target is unreachable.
            PublisherSerializationError: If a record cannot be serialized.
        """
        ...
