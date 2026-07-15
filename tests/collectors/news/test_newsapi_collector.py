"""
tests/collectors/news/test_newsapi_collector.py
===============================================
Unit tests for the NewsApiCollector class.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from intelligence_layer.collectors.news.newsapi_collector import NewsApiCollector
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.exceptions import (
    CollectorConnectionError,
    CollectorParseError,
    CollectorTimeoutError,
)


@pytest.fixture
def sample_response_data() -> dict:
    """Fixture to load the NewsAPI sample response JSON file."""
    fixture_path = (
        Path(__file__).resolve().parents[2] / "fixtures" / "raw" / "newsapi_sample_response.json"
    )
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def default_source_config() -> SourceConfig:
    """Fixture for standard SourceConfig for NewsAPI."""
    return SourceConfig(
        source_id="newsapi_test",
        enabled=True,
        poll_interval_seconds=300,
        timeout_seconds=5,
        max_retries=2,
        extra={
            "api_key": "test-api-key-12345",
            "base_url": "https://newsapi.org/v2/everything",
            "page_size": "20",
            "sort_by": "publishedAt",
            "language": "en",
            "retry_backoff_seconds": "0.01",  # low backoff for fast tests
            "filters_config": "newsapi_filters.yaml",
        },
    )


def test_collector_source_id(default_source_config: SourceConfig) -> None:
    """Test source_id property of the collector."""
    collector = NewsApiCollector(default_source_config)
    assert collector.source_id == "newsapi_test"
    assert collector.page_size == 20
    assert collector.sort_by == "publishedAt"
    assert collector.language == "en"
    assert collector.api_key == "test-api-key-12345"


def test_collector_missing_api_key() -> None:
    """Test that ValueError is raised when no API key is provided."""
    config = SourceConfig(
        source_id="newsapi_no_key",
        extra={"filters_config": "newsapi_filters.yaml"},
    )
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="NewsAPI key not found"):
            NewsApiCollector(config)


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_success(
    mock_get: MagicMock, default_source_config: SourceConfig, sample_response_data: dict
) -> None:
    """Test successful raw data collection from NewsAPI."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_response_data
    mock_get.return_value = mock_response

    collector = NewsApiCollector(default_source_config)
    result = collector.collect()

    assert result == sample_response_data
    assert result["status"] == "ok"
    assert len(result["articles"]) == 2

    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["headers"]["X-Api-Key"] == "test-api-key-12345"


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_http_401_unauthorized(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector behavior on 401 Unauthorized (bad API key)."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.reason = "Unauthorized"
    mock_response.json.return_value = {
        "status": "error",
        "code": "apiKeyInvalid",
        "message": "Your API key is invalid or incorrect.",
    }
    mock_get.return_value = mock_response

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "401" in str(exc_info.value)
    # 401 is non-transient, should fail immediately without retries
    assert mock_get.call_count == 1


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_http_429_rate_limit(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector retries on 429 rate limit and eventually raises."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_get.return_value = mock_response

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "rate limit" in str(exc_info.value).lower()
    # max_retries=2 means 3 total attempts
    assert mock_get.call_count == 3


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_timeout_error(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector raises CollectorTimeoutError after timeout retries fail."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorTimeoutError) as exc_info:
        collector.collect()

    assert "timed out" in str(exc_info.value).lower()
    assert mock_get.call_count == 3


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_connection_error(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector raises CollectorConnectionError after network failure retries."""
    mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "Failed to connect" in str(exc_info.value)
    assert mock_get.call_count == 3


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_parse_error(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector raises CollectorParseError when response is not valid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("No JSON object could be decoded")
    mock_response.text = "<html>Error</html>"
    mock_get.return_value = mock_response

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorParseError) as exc_info:
        collector.collect()

    assert "Failed to parse JSON" in str(exc_info.value)
    assert mock_get.call_count == 1


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_api_error_in_body(
    mock_get: MagicMock, default_source_config: SourceConfig
) -> None:
    """Test collector handles NewsAPI error returned inside a 200 response body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "error",
        "code": "parametersMissing",
        "message": "Required parameters are missing.",
    }
    mock_get.return_value = mock_response

    collector = NewsApiCollector(default_source_config)

    with pytest.raises(CollectorConnectionError) as exc_info:
        collector.collect()

    assert "parametersMissing" in str(exc_info.value)
    assert mock_get.call_count == 1


@patch("intelligence_layer.collectors.news.newsapi_collector.requests.get")
def test_collect_retry_on_5xx_success(
    mock_get: MagicMock, default_source_config: SourceConfig, sample_response_data: dict
) -> None:
    """Test collector retries on transient server error (500) and then succeeds."""
    mock_response_err = MagicMock()
    mock_response_err.status_code = 500
    mock_response_err.reason = "Internal Server Error"
    mock_response_err.text = "Temporary breakdown"

    mock_response_ok = MagicMock()
    mock_response_ok.status_code = 200
    mock_response_ok.json.return_value = sample_response_data

    mock_get.side_effect = [mock_response_err, mock_response_ok]

    collector = NewsApiCollector(default_source_config)
    result = collector.collect()

    assert result == sample_response_data
    assert mock_get.call_count == 2
