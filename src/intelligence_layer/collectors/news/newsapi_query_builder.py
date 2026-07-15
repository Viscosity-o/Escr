"""
collectors/news/newsapi_query_builder.py
=========================================
Builds NewsAPI-compatible query strings from the shared filter
configuration YAML.

NewsAPI's ``/v2/everything`` endpoint accepts a ``q`` parameter that
supports AND/OR operators and double-quoted exact phrases — very similar
to GDELT's query syntax.

This module reuses ``load_filter_config`` from the existing query_builder
so that both GDELT and NewsAPI collectors share the same filter vocabulary.
"""
from pathlib import Path

from intelligence_layer.collectors.news.query_builder import load_filter_config
from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)


def _quote_term(term: str) -> str:
    """
    Wrap a term in double quotes if it contains spaces.

    Single-word terms are left unquoted, matching NewsAPI query syntax.

    Args:
        term: A single search term.

    Returns:
        The term, optionally wrapped in double quotes.
    """
    if " " in term:
        return f'"{term}"'
    return term


def build_newsapi_query(terms: list[str]) -> str:
    """
    Build a NewsAPI query string from a list of terms.

    All terms are OR'd together.  NewsAPI does not require parenthesized
    groups for simple OR queries, but we add them for clarity and safety.

    Example output::

        "crude oil" OR "oil production" OR LNG OR refinery

    Args:
        terms: Deduplicated list of search terms.

    Returns:
        A ready-to-use NewsAPI query string.

    Raises:
        ValueError: If the terms list is empty.
    """
    if not terms:
        raise ValueError("Cannot build a NewsAPI query with an empty terms list.")

    quoted = [_quote_term(t) for t in terms]
    query = " OR ".join(quoted)

    logger.debug("Built NewsAPI query (%d chars): %s", len(query), query[:200])
    return query


def build_newsapi_query_from_config(config_path: Path) -> str:
    """
    High-level convenience: load filters and build the query in one call.

    Flattens all filter groups into a single OR'd query string.

    Args:
        config_path: Path to the filters YAML file.

    Returns:
        A ready-to-use NewsAPI query string.
    """
    config = load_filter_config(config_path)
    filter_groups: dict[str, list[str]] = config.get("filter_groups", {})

    seen: set[str] = set()
    terms: list[str] = []
    for group_terms in filter_groups.values():
        for term in group_terms:
            normalized = term.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                terms.append(normalized)

    return build_newsapi_query(terms)


def get_filter_group_names(config_path: Path) -> list[str]:
    """
    Return the list of filter group names defined in the config file.

    Args:
        config_path: Path to the filters YAML file.

    Returns:
        List of group name strings.
    """
    config = load_filter_config(config_path)
    filter_groups: dict[str, list[str]] = config.get("filter_groups", {})
    return list(filter_groups.keys())


def build_newsapi_query_for_group(
    config_path: Path,
    group_name: str,
    max_terms: int = 6,
) -> str:
    """
    Build a NewsAPI query using only the first ``max_terms`` terms from a
    single filter group.

    Useful for dry-run / testing scenarios where sending one smaller query
    per group avoids potential rate limits.

    Args:
        config_path: Path to the filters YAML file.
        group_name: Key of the filter group to use (must exist in the config).
        max_terms: Maximum number of terms to include from the group.

    Returns:
        A ready-to-use NewsAPI query string.

    Raises:
        KeyError: If ``group_name`` is not found in the config's filter_groups.
        ValueError: If the group exists but has no terms.
    """
    config = load_filter_config(config_path)
    filter_groups: dict[str, list[str]] = config.get("filter_groups", {})

    if group_name not in filter_groups:
        available = ", ".join(filter_groups.keys())
        raise KeyError(
            f"Filter group '{group_name}' not found. Available groups: {available}"
        )

    raw_terms = filter_groups[group_name]
    seen: set[str] = set()
    terms: list[str] = []
    for term in raw_terms:
        normalized = term.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            terms.append(normalized)
        if len(terms) >= max_terms:
            break

    logger.debug(
        "Building NewsAPI query for group '%s': using %d/%d terms (max_terms=%d)",
        group_name,
        len(terms),
        len(raw_terms),
        max_terms,
    )
    return build_newsapi_query(terms)
