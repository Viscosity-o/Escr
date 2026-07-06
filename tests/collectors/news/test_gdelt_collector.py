"""
tests/collectors/news/test_gdelt_collector.py
=============================================
Unit tests for the GdeltCollector class.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from intelligence_layer.collectors.news.gdelt_collector import GdeltCollector
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.exceptions import (
    CollectorConnectionError,
    CollectorParseError,
    CollectorTimeoutError,
)


@pytest.fixture
def sample_response_data() -> dict:
    """Fixture to load the GDELT sample response JSON file."""
    fixture_path = (
        Path(__file__).resolve().parents[2] / "fixtures" / "raw" / "gdelt_sample_response.json"
    )
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def default_source_config() -> SourceConfig:
    """Fixture for standard SourceConfig for GDELT."""
    return SourceConfig(
        source_id="gdelt_news",
        enabled=True,
        poll_interval_seconds=300,
        timeout_seconds=5,
        max_retries=2,
        extra={
            "base_url": "https://api.gdeltproject.org/api/v2/doc/doc",
            "max_records": "250",
            "mode": "artlist",
            "format": "json",
            "retry_backoff_seconds": "0.1",  # low backoff for fast tests
            "filters_config": "gdelt_filters.yaml",
        },
    )


def test_collector_source_id(default_source_config: SourceConfig) -> None:
    """Test source_id property of the collector."""
    collector = GdeltCollector(default_source_config)
    assert collector.source_id == "gdelt_news"
    assert collector.max_records == 250
    assert collector.api_mode == "artlist"
    assert collector.response_format == "json"
    assert collector.retry_backoff_seconds == 0.1


@patch("requests.get")
def test_collect_success(
    mock_get: MagicMock, default_source_config: SourceConfig, sample_response_data: dict
) -> None:
    """Test successful raw data collection from GDELT API."""
    # Set up mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_response_data
    mock_get.return_value = mock_response

    collector = GdeltCollector(default_source_config)
    result = collector.collect()

    assert result == sample_response_data
    assert "articles" in result
    assert len(result["articles"]) == 2
    mock_get.assert_called_once_with(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": collector.query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": 250,
        },
        timeout=5,
    )


@patch("requests.get")
def test_collect_http_error(mock_get: MagicMock, default_source_config: SourceConfig) -> None:
    """Test collector behavior on non-200 HTTP status code."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Error detail message"
    mock_get.return_value = mock_response

    collector = GdeltCollector(default_source_config)

    # 404 is non-transient, should fail immediately without retries
    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "GDELT API returned HTTP error: 404" in str(exc_info.value)
    assert mock_get.call_count == 1


@patch("requests.get")
def test_collect_timeout_error(mock_get: MagicMock, default_source_config: SourceConfig) -> None:
    """Test collector raises CollectorTimeoutError after timeout retries fail."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    collector = GdeltCollector(default_source_config)

    with pytest.raises(CollectorTimeoutError) as exc_info:
        collector.collect()

    assert "GDELT API request timed out" in str(exc_info.value)
    # max_retries = 2, meaning 3 attempts total (initial + 2 retries)
    assert mock_get.call_count == 3


@patch("requests.get")
def test_collect_connection_error(mock_get: MagicMock, default_source_config: SourceConfig) -> None:
    """Test collector raises CollectorConnectionError after generic network failure retries fail."""
    mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")

    collector = GdeltCollector(default_source_config)

    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "Failed to connect to GDELT API" in str(exc_info.value)
    assert mock_get.call_count == 3


@patch("requests.get")
def test_collect_parse_error(mock_get: MagicMock, default_source_config: SourceConfig) -> None:
    """Test collector raises CollectorParseError when response is not valid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("No JSON object could be decoded")
    mock_get.return_value = mock_response

    collector = GdeltCollector(default_source_config)

    with pytest.raises(CollectorParseError) as exc_info:
        collector.collect()

    assert "Failed to parse JSON response" in str(exc_info.value)
    assert mock_get.call_count == 1


@patch("requests.get")
def test_collect_retry_on_5xx_success(
    mock_get: MagicMock, default_source_config: SourceConfig, sample_response_data: dict
) -> None:
    """Test collector retries on transient server error (500) and then succeeds."""
    # First response is a 500 error, second response is successful 200
    mock_response_err = MagicMock()
    mock_response_err.status_code = 500
    mock_response_err.reason = "Internal Server Error"
    mock_response_err.text = "Temporary breakdown"

    mock_response_ok = MagicMock()
    mock_response_ok.status_code = 200
    mock_response_ok.json.return_value = sample_response_data

    mock_get.side_effect = [mock_response_err, mock_response_ok]

    collector = GdeltCollector(default_source_config)
    result = collector.collect()

    assert result == sample_response_data
    assert mock_get.call_count == 2
