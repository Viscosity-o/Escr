"""
collectors/
===========
Houses all data collection components, one sub-package per data source category.

Each collector is responsible for:
  - Connecting to a single external source
  - Fetching raw data
  - Returning it without any transformation or business logic

New data sources should be added as new sub-packages here, implementing
the base interface defined in collectors/base.py.
"""
