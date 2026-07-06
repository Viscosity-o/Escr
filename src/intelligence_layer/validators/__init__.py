"""
validators/
===========
Responsible for validating raw data immediately after collection,
before any transformation occurs.

Validation checks include:
  - Presence of required fields
  - Correct data types
  - Value range checks (e.g., timestamps not in the future)
  - Format conformity (e.g., valid ISO dates, non-empty strings)

Validators do NOT transform data. They only accept or reject it,
and produce structured validation results for observability.

Each data source category should have a corresponding validator module
mirroring the collectors/ structure.
"""
