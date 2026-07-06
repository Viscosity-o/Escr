"""
tests/collectors/news/test_query_builder.py
============================================
Unit tests for the query_builder module.
"""
from pathlib import Path

import pytest

from intelligence_layer.collectors.news.query_builder import (
    build_gdelt_query,
    build_query_from_config,
    extract_all_terms,
    load_filter_config,
)


def test_load_filter_config(tmp_path: Path) -> None:
    """Test loading valid filter config YAML file."""
    yaml_content = """
source_language: English
filter_groups:
  group1:
    - "term1"
    - "term2"
"""
    config_file = tmp_path / "test_filters.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    config = load_filter_config(config_file)
    assert config["source_language"] == "English"
    assert config["filter_groups"]["group1"] == ["term1", "term2"]


def test_load_filter_config_not_found() -> None:
    """Test FileNotFoundError is raised if file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_filter_config(Path("non_existent_file.yaml"))


def test_extract_all_terms() -> None:
    """Test flattening and deduplicating terms from groups."""
    filter_groups = {
      "group1": ["crude oil", "refinery"],
      "group2": ["sanctions", "crude oil", "  Strait of Hormuz  "],
      "group3": ["", "  "] # Empty terms
    }

    terms = extract_all_terms(filter_groups)
    assert terms == ["crude oil", "refinery", "sanctions", "Strait of Hormuz"]


def test_build_gdelt_query() -> None:
    """Test GDELT query construction with quoting and language."""
    terms = ["crude oil", "refinery", "Strait of Hormuz", "OPEC"]

    query = build_gdelt_query(terms, source_language="English")
    # Multi-word terms should be quoted, single-word unquoted
    expected = '("crude oil" OR refinery OR "Strait of Hormuz" OR OPEC) sourcelang:English'
    assert query == expected


def test_build_gdelt_query_empty() -> None:
    """Test ValueError is raised when building query with empty terms."""
    with pytest.raises(ValueError, match="Cannot build a GDELT query with an empty terms list"):
        build_gdelt_query([])


def test_build_query_from_config(tmp_path: Path) -> None:
    """Test convenience function that wraps config loading and query building."""
    yaml_content = """
source_language: Spanish
filter_groups:
  group_a:
    - "oil spill"
  group_b:
    - "tanker"
"""
    config_file = tmp_path / "test_filters.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    query = build_query_from_config(config_file)
    assert query == '("oil spill" OR tanker) sourcelang:Spanish'
