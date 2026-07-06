"""
collectors/news/query_builder.py
=================================
Loads filter configuration from YAML and builds a single optimized
GDELT DOC 2.0 API query string.

This module is intentionally separated from the collector so that:
  - Query construction can be tested independently.
  - Future GDELT-based collectors can reuse the same builder.
  - Filter logic stays isolated from HTTP/connection concerns.
"""
from pathlib import Path
from typing import Any

import yaml

from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)


def load_filter_config(config_path: Path) -> dict[str, Any]:
    """
    Read and return the full filter configuration from a YAML file.

    Args:
        config_path: Absolute path to the GDELT filters YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    logger.debug("Loading GDELT filter config from %s", config_path)

    with open(config_path, encoding="utf-8") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    return config


def extract_all_terms(filter_groups: dict[str, list[str]]) -> list[str]:
    """
    Flatten all filter groups into a single deduplicated list of terms.

    Preserves insertion order while removing duplicates (a term appearing
    in multiple groups is included only once).

    Args:
        filter_groups: Mapping of group name → list of search terms.

    Returns:
        Deduplicated list of all terms across all groups.
    """
    seen: set[str] = set()
    terms: list[str] = []

    for group_name, group_terms in filter_groups.items():
        for term in group_terms:
            normalized = term.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                terms.append(normalized)

    logger.debug(
        "Extracted %d unique terms from %d filter groups",
        len(terms),
        len(filter_groups),
    )
    return terms


def _quote_term(term: str) -> str:
    """
    Wrap a term in double quotes if it contains spaces.

    Single-word terms are left unquoted, matching GDELT query syntax.

    Args:
        term: A single search term.

    Returns:
        The term, optionally wrapped in double quotes.
    """
    if " " in term:
        return f'"{term}"'
    return term


def build_gdelt_query(terms: list[str], source_language: str = "English") -> str:
    """
    Build a single optimized GDELT query string from a list of terms.

    All terms are OR'd together in a parenthesized group, and a
    ``sourcelang`` filter is appended to restrict results by language.

    Example output::

        ("crude oil" OR sanctions OR "Strait of Hormuz") sourcelang:English

    Args:
        terms: Deduplicated list of search terms.
        source_language: Language filter for GDELT (default: English).

    Returns:
        A ready-to-use GDELT query string.

    Raises:
        ValueError: If the terms list is empty.
    """
    if not terms:
        raise ValueError("Cannot build a GDELT query with an empty terms list.")

    quoted = [_quote_term(t) for t in terms]
    query = f"({' OR '.join(quoted)}) sourcelang:{source_language}"

    logger.debug("Built GDELT query (%d chars): %s", len(query), query[:200])
    return query


def build_query_from_config(config_path: Path) -> str:
    """
    High-level convenience: load filters and build the query in one call.

    This is the primary entry point used by the collector.

    Args:
        config_path: Path to the GDELT filters YAML file.

    Returns:
        A ready-to-use GDELT query string.
    """
    config = load_filter_config(config_path)
    filter_groups: dict[str, list[str]] = config.get("filter_groups", {})
    source_language: str = config.get("source_language", "English")

    terms = extract_all_terms(filter_groups)
    return build_gdelt_query(terms, source_language)
