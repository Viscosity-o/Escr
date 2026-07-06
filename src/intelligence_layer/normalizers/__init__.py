"""
normalizers/
============
Transforms validated raw data into a consistent, source-agnostic
internal format (IntelligenceRecord) that downstream systems can rely on.

Normalization responsibilities:
  - Field mapping (source field names → canonical field names)
  - Type coercion (strings → datetimes, numbers, enums)
  - Unit standardization (e.g., all prices in USD, all timestamps in UTC ISO-8601)
  - Optional enrichment with metadata (source_id, collection_timestamp, etc.)

Normalizers do NOT validate data — that is the validators' responsibility.
Normalizers assume the data they receive has already passed validation.

Each data source category should have a corresponding normalizer module
mirroring the collectors/ structure.
"""
