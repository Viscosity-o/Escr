"""
validators/base.py
==================
Defines the abstract base interface and result contract for all validators.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """
    The outcome of a validation pass on a single raw data payload.

    Attributes:
        is_valid:  True if the data passed all checks.
        errors:    List of human-readable error messages (empty if valid).
        warnings:  Non-fatal issues that do not block processing.
        source_id: The collector source this data originated from.
    """

    is_valid: bool
    source_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseValidator(ABC):
    """
    Abstract base class for all data validators.

    Each validator is tightly coupled to one data source category
    and knows the expected raw structure for that source.
    """

    @abstractmethod
    def validate(self, raw_data: Any) -> ValidationResult:
        """
        Validate a raw data payload.

        Args:
            raw_data: The raw object returned by a collector.

        Returns:
            A ValidationResult describing pass/fail and any issues found.
        """
        ...
