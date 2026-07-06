"""
models/
=======
Defines the internal data models and schemas used throughout the module.

These are plain Python data structures (dataclasses or similar) — they are
NOT tied to any ORM, database, or serialization framework.

The canonical model is IntelligenceRecord, which is the normalized
output format shared across validators, normalizers, and publishers.

Additional models cover:
  - Source metadata
  - Validation result contracts
  - Enumerations (data source categories, data types, etc.)
"""
