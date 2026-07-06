"""
utils/
======
Shared utility functions and helpers used across the module.

Utilities are pure, stateless, and have no knowledge of business logic.
They solve common cross-cutting concerns such as:
  - Logging setup
  - Configuration loading
  - Date/time handling
  - String sanitization
  - HTTP request helpers (retry wrappers, header builders)
  - Exception definitions

Nothing in utils/ should import from collectors/, validators/,
normalizers/, or publishers/. Dependencies flow one way only.
"""
