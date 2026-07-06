"""
models/intelligence_record.py
==============================
The canonical normalized data model for the Global Intelligence Layer.

Every piece of external intelligence — regardless of its source — is
mapped into an IntelligenceRecord before being forwarded downstream.
This ensures downstream systems receive a consistent, predictable schema.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DataSourceCategory(str, Enum):
    """High-level category of the originating data source."""

    NEWS = "news"
    MARITIME = "maritime"
    SANCTIONS = "sanctions"
    COMMODITIES = "commodities"
    CONFLICT = "conflict"
    WEATHER = "weather"
    OTHER = "other"


@dataclass
class IntelligenceRecord:
    """
    The normalized, source-agnostic representation of a single intelligence item.

    Attributes:
        record_id:           Unique identifier for this record (auto-generated).
        source_id:           The collector's source_id that produced this record.
        source_category:     High-level category of the data source.
        collected_at:        UTC timestamp when the raw data was collected.
        published_at:        UTC timestamp when the original item was published
                             by the source (may be None if unavailable).
        title:               A short human-readable summary or headline.
        content:             Full or truncated body content.
        url:                 Source URL, if applicable.
        geo_references:      List of geographic entities mentioned (country codes,
                             region names, coordinates, etc.).
        tags:                Free-form keyword tags for routing and filtering.
        raw_metadata:        Additional source-specific fields that do not map
                             to canonical fields — preserved for traceability.
    """

    source_id: str
    source_category: DataSourceCategory
    collected_at: datetime
    title: str
    content: str

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    published_at: datetime | None = None
    url: str | None = None
    geo_references: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)
