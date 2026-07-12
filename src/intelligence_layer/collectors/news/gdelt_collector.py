"""
collectors/news/gdelt_collector.py
==================================
GdeltCollector class implements the BaseCollector interface to fetch
news articles from the GDELT 2.0 DOC API.

This collector builds a single optimized query string from the configuration
groups, establishes a connection using the requests library, and handles
retries, timeouts, and exception mapping cleanly.
"""
import time
from typing import Any

import requests

from intelligence_layer.collectors.base import BaseCollector
from intelligence_layer.collectors.news.query_builder import build_query_from_config
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.config_loader import get_config_path
from intelligence_layer.utils.exceptions import (
    CollectorConnectionError,
    CollectorParseError,
    CollectorTimeoutError,
)
from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)


class GdeltCollector(BaseCollector):
    """
    Collector implementation for the official GDELT 2.0 DOC API.
    """

    def __init__(self, config: SourceConfig) -> None:
        """
        Initialize the GDELT news collector with a SourceConfig.

        Args:
            config: Operational configuration for the collector.
        """
        self._config = config

        # Resolve filter config filename from config.extra or default to gdelt_filters.yaml
        filters_filename = self._config.extra.get("filters_config", "gdelt_filters.yaml")
        self.filters_path = get_config_path(filters_filename)

        # Build GDELT query from the config groups
        self.query = build_query_from_config(self.filters_path)

        # Load operational parameter overrides from extra
        self.base_url = self._config.extra.get(
            "base_url", "https://api.gdeltproject.org/api/v2/doc/doc"
        )
        self.max_records = int(self._config.extra.get("max_records", "10"))
        self.api_mode = self._config.extra.get("mode", "artlist")
        self.response_format = self._config.extra.get("format", "json")

        try:
            self.retry_backoff_seconds = float(
                self._config.extra.get("retry_backoff_seconds", "5.0")
            )
        except ValueError:
            self.retry_backoff_seconds = 5.0

    @property
    def source_id(self) -> str:
        """
        Return the unique identifier for this source.
        """
        return self._config.source_id

    def collect(self) -> Any:
        """
        Fetch raw data from the GDELT DOC API.

        Returns:
            The raw response dict parsed from the GDELT JSON payload.

        Raises:
            CollectorConnectionError: If the API cannot be reached or returns a non-2xx status code.
            CollectorTimeoutError: If the API request times out.
            CollectorParseError: If the API response cannot be decoded as JSON.
        """
        # Prepare request query parameters
        params: dict[str, str | int] = {
            "query": self.query,
            "mode": self.api_mode,
            "format": self.response_format,
            "maxrecords": self.max_records,
        }

        max_retries = self._config.max_retries
        timeout = self._config.timeout_seconds

        logger.info(
            "Request started: fetching GDELT data from url=%s with query=%s",
            self.base_url,
            self.query,
        )

        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=timeout,
                )

                # Detect rate limiting (either via 429 status or rate limit message in text)
                is_rate_limited = (response.status_code == 429) or (
                    "Please limit requests" in response.text
                )
                is_server_error = response.status_code >= 500

                if is_rate_limited or is_server_error:
                    error_msg = f"HTTP {response.status_code}: {response.text.strip()}"
                    logger.warning(
                        "Attempt %d/%d failed with transient error: %s",
                        attempt + 1,
                        max_retries + 1,
                        error_msg,
                    )
                    if attempt < max_retries:
                        # Extra backoff: wait slightly longer for rate limit recovery
                        sleep_time = self.retry_backoff_seconds * (2**attempt)
                        if is_rate_limited:
                            # GDELT explicitly asks for at least 5s
                            sleep_time = max(sleep_time, 5.0)
                        time.sleep(sleep_time)
                        continue

                    if is_rate_limited:
                        raise CollectorConnectionError(
                            f"GDELT API rate limit exceeded: {error_msg}"
                        )
                    else:
                        raise CollectorConnectionError(f"GDELT API server error: {error_msg}")

                if response.status_code != 200:
                    raise CollectorConnectionError(
                        f"GDELT API returned HTTP error: {response.status_code} - {response.reason}"
                    )

                # Decode JSON response
                try:
                    data = response.json()
                except ValueError as err:
                    # If response is invalid JSON (e.g. HTML error page) and we have retries, retry
                    is_invalid_content = (
                        "<html" in response.text.lower()
                        or "error" in response.text.lower()
                    )
                    if is_invalid_content and attempt < max_retries:
                        logger.warning(
                            "Attempt %d/%d returned invalid JSON/HTML content. Retrying...",
                            attempt + 1,
                            max_retries + 1,
                        )
                        time.sleep(self.retry_backoff_seconds * (2**attempt))
                        continue
                    raise CollectorParseError(
                        f"Failed to parse JSON response from GDELT API: {err}. "
                        f"Raw response: {response.text[:200]}"
                    ) from err

                num_articles = len(data.get("articles", []))
                logger.info(
                    "Request succeeded: fetched %d articles from GDELT",
                    num_articles,
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
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise CollectorTimeoutError(
                    f"GDELT API request timed out after {timeout} seconds"
                ) from err

            except requests.exceptions.RequestException as err:
                logger.warning(
                    "Attempt %d/%d connection error: %s",
                    attempt + 1,
                    max_retries + 1,
                    err,
                )
                if attempt < max_retries:
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise CollectorConnectionError(
                    f"Failed to connect to GDELT API: {err}"
                ) from err

        # If retries exceeded, raise an error
        raise CollectorConnectionError(
            f"All {max_retries + 1} attempts to GDELT API failed."
        )
