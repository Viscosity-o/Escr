"""
utils/exceptions.py
====================
Custom exception hierarchy for the Global Intelligence Layer.

Using a dedicated exception hierarchy allows callers to catch errors
at the right level of granularity without coupling to implementation details.
"""


class IntelligenceLayerError(Exception):
    """Base exception for all errors raised within this module."""


# ── Collector Errors ──────────────────────────────────────────────────────────

class CollectorError(IntelligenceLayerError):
    """Base class for all collection-related errors."""


class CollectorConnectionError(CollectorError):
    """Raised when a collector cannot reach its external source."""


class CollectorParseError(CollectorError):
    """Raised when a collector cannot read or decode a source response."""


class CollectorTimeoutError(CollectorError):
    """Raised when a collection attempt exceeds the configured timeout."""


# ── Validator Errors ──────────────────────────────────────────────────────────

class ValidatorError(IntelligenceLayerError):
    """Base class for all validation-related errors."""


# ── Normalizer Errors ─────────────────────────────────────────────────────────

class NormalizerError(IntelligenceLayerError):
    """Base class for all normalization-related errors."""


class NormalizerMappingError(NormalizerError):
    """Raised when a required field cannot be mapped during normalization."""


# ── Publisher Errors ──────────────────────────────────────────────────────────

class PublisherError(IntelligenceLayerError):
    """Base class for all publishing-related errors."""


class PublisherConnectionError(PublisherError):
    """Raised when the downstream target is unreachable."""


class PublisherSerializationError(PublisherError):
    """Raised when an IntelligenceRecord cannot be serialized for transport."""
