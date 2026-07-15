"""
collectors/news/newsapi_collector.py
=====================================
NewsApiCollector implements the BaseCollector interface to fetch
news articles from the NewsAPI.org /v2/everything endpoint.

This collector builds a keyword query from the configuration groups,
sends it with appropriate parameters, and handles retries, timeouts,
and exception mapping cleanly.
"""
import os
import random
import time
from typing import Any

import requests

from intelligence_layer.collectors.base import BaseCollector
from intelligence_layer.collectors.news.newsapi_query_builder import (
    build_newsapi_query_from_config,
)
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.config_loader import get_config_path
from intelligence_layer.utils.exceptions import (
    CollectorConnectionError,
    CollectorParseError,
    CollectorTimeoutError,
)
from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)

# Default base URL for NewsAPI
_DEFAULT_BASE_URL = "https://newsapi.org/v2/everything"


class NewsApiCollector(BaseCollector):
    """
    Collector implementation for the NewsAPI.org /v2/everything endpoint.
    """

    def __init__(self, config: SourceConfig) -> None:
        """
        Initialize the NewsAPI collector with a SourceConfig.

        The API key is resolved from (in priority order):
          1. config.extra["api_key"]
          2. The NEWSAPI_KEY environment variable

        Args:
            config: Operational configuration for the collector.

        Raises:
            ValueError: If no API key is found.
        """
        self._config = config

        # Resolve API key
        self.api_key = self._config.extra.get("api_key") or os.environ.get("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError(
                "NewsAPI key not found. Set it via config.extra['api_key'] "
                "or the NEWSAPI_KEY environment variable."
            )

        # Resolve filter config filename
        filters_filename = self._config.extra.get("filters_config", "newsapi_filters.yaml")
        self.filters_path = get_config_path(filters_filename)

        # Build the keyword query from all filter groups
        self.query = build_newsapi_query_from_config(self.filters_path)

        # Load operational parameter overrides from extra
        self.base_url = self._config.extra.get("base_url", _DEFAULT_BASE_URL)
        self.page_size = int(self._config.extra.get("page_size", "20"))
        self.sort_by = self._config.extra.get("sort_by", "publishedAt")
        self.language = self._config.extra.get("language", "en")

        try:
            self.retry_backoff_seconds = float(
                self._config.extra.get("retry_backoff_seconds", "2.0")
            )
        except ValueError:
            self.retry_backoff_seconds = 2.0

    @property
    def source_id(self) -> str:
        """
        Return the unique identifier for this source.
        """
        return self._config.source_id

    def collect(self) -> Any:
        """
        Fetch raw data from the NewsAPI /v2/everything endpoint.

        Returns:
            The raw response dict parsed from the NewsAPI JSON payload.

        Raises:
            CollectorConnectionError: If the API cannot be reached or returns an error.
            CollectorTimeoutError: If the API request times out.
            CollectorParseError: If the API response cannot be decoded as JSON.
        """
        params: dict[str, str | int] = {
            "q": self.query,
            "language": self.language,
            "sortBy": self.sort_by,
            "pageSize": self.page_size,
        }

        headers: dict[str, str] = {
            "X-Api-Key": self.api_key,
        }

        max_retries = self._config.max_retries
        timeout = self._config.timeout_seconds

        logger.info(
            "[%s] Request started: fetching news from url=%s with query=%s",
            self.source_id,
            self.base_url,
            self.query[:200],
        )

        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )

                # ── Handle rate limiting (429) ────────────────────────────
                if response.status_code == 429:
                    error_msg = f"HTTP 429: {response.text.strip()}"
                    logger.warning(
                        "Attempt %d/%d rate limited: %s",
                        attempt + 1,
                        max_retries + 1,
                        error_msg,
                    )
                    if attempt < max_retries:
                        sleep_time = max(
                            self.retry_backoff_seconds * (2 ** attempt), 7.0
                        )
                        sleep_time += random.uniform(0, 3.0)
                        time.sleep(sleep_time)
                        continue
                    raise CollectorConnectionError(
                        f"NewsAPI rate limit exceeded: {error_msg}"
                    )

                # ── Handle server errors (5xx) ────────────────────────────
                if response.status_code >= 500:
                    error_msg = f"HTTP {response.status_code}: {response.text.strip()}"
                    logger.warning(
                        "Attempt %d/%d server error: %s",
                        attempt + 1,
                        max_retries + 1,
                        error_msg,
                    )
                    if attempt < max_retries:
                        sleep_time = self.retry_backoff_seconds * (2 ** attempt)
                        time.sleep(sleep_time)
                        continue
                    raise CollectorConnectionError(
                        f"NewsAPI server error: {error_msg}"
                    )

                # ── Handle client errors (4xx) ────────────────────────────
                if response.status_code != 200:
                    # Try to extract a meaningful error message from the JSON body
                    try:
                        error_body = response.json()
                        api_message = error_body.get("message", response.reason)
                    except (ValueError, AttributeError):
                        api_message = response.reason

                    raise CollectorConnectionError(
                        f"NewsAPI returned HTTP {response.status_code}: {api_message}"
                    )

                # ── Decode JSON response ──────────────────────────────────
                try:
                    data = response.json()
                except ValueError as err:
                    raise CollectorParseError(
                        f"Failed to parse JSON response from NewsAPI: {err}. "
                        f"Raw response: {response.text[:200]}"
                    ) from err

                # NewsAPI wraps errors inside a 200 response with status="error"
                if data.get("status") == "error":
                    api_code = data.get("code", "unknown")
                    api_message = data.get("message", "Unknown error")
                    raise CollectorConnectionError(
                        f"NewsAPI returned error: [{api_code}] {api_message}"
                    )

                num_articles = len(data.get("articles", []))
                total_results = data.get("totalResults", 0)
                logger.info(
                    "[%s] Request succeeded: fetched %d articles (totalResults=%d)",
                    self.source_id,
                    num_articles,
                    total_results,
                )
                return data

            except requests.exceptions.Timeout as err:
                logger.warning(
                    "Attempt %d/%d timed out after %d seconds: %s",
                    attempt + 1,
                    max_retries + 1,
                    timeout,
                    err,
                )
                if attempt < max_retries:
                    time.sleep(self.retry_backoff_seconds * (2 ** attempt))
                    continue
                raise CollectorTimeoutError(
                    f"NewsAPI request timed out after {timeout} seconds"
                ) from err

            except requests.exceptions.RequestException as err:
                logger.warning(
                    "Attempt %d/%d connection error: %s",
                    attempt + 1,
                    max_retries + 1,
                    err,
                )
                if attempt < max_retries:
                    time.sleep(self.retry_backoff_seconds * (2 ** attempt))
                    continue
                raise CollectorConnectionError(
                    f"Failed to connect to NewsAPI: {err}"
                ) from err

        # Should not be reached, but just in case
        raise CollectorConnectionError(
            f"All {max_retries + 1} attempts to NewsAPI failed."
        )
