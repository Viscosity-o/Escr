"""
commodity_collector.py

Implements CommodityCollector: the collector responsible for fetching
raw commodity market data from Yahoo Finance.

Follows the same architecture and style as GdeltCollector — it
consumes an already-parsed configuration (via commodity_loader.py),
performs the network call with exponential-backoff retry and timeout
handling, and returns structured raw records (not a raw DataFrame,
not normalized/enriched data).
"""

import time
from typing import Any

import yfinance as yf

from intelligence_layer.collectors.commodities.Commodity_loader import load_commodity_config
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.config_loader import get_config_path
from intelligence_layer.utils.exceptions import (
    CollectorConnectionError,
    CollectorTimeoutError,
    CollectorParseError,
)
from intelligence_layer.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_RETRY_BACKOFF_SECONDS = 2.0


class CommodityCollector:
    """
    Collector for commodity market data sourced from Yahoo Finance.

    Reads its configuration filename from `config.extra["commodities_config"]`,
    resolves it to a full path, loads and validates it via
    `load_commodity_config`, and uses the resulting symbol list to
    fetch market data. Returns structured raw records — one dict per
    symbol per timestamp — with no normalization or enrichment applied.
    """

    def __init__(self, config: SourceConfig) -> None:
        """
        Args:
            config: The SourceConfig for this collector. Must contain
                the commodities YAML filename under
                `config.extra["commodities_config"]`. Retry backoff is
                read from `config.extra["retry_backoff_seconds"]` since
                SourceConfig itself does not define that field.
        """
        self._config = config
        self._retry_backoff_seconds = self._resolve_retry_backoff(config)

    @staticmethod
    def _resolve_retry_backoff(config: SourceConfig) -> float:
        """
        Reads `retry_backoff_seconds` from `config.extra`, converting
        it to a float. Falls back to a sensible default if the key is
        missing or the value can't be converted.

        Args:
            config: The SourceConfig to read from.

        Returns:
            The retry backoff, in seconds, as a float.
        """
        raw_value = config.extra.get("retry_backoff_seconds")
        try:
            return float(raw_value) if raw_value is not None else DEFAULT_RETRY_BACKOFF_SECONDS
        except (TypeError, ValueError):
            logger.warning(
                f"[{config.source_id}] Invalid retry_backoff_seconds "
                f"'{raw_value}' — falling back to default "
                f"{DEFAULT_RETRY_BACKOFF_SECONDS}s"
            )
            return DEFAULT_RETRY_BACKOFF_SECONDS

    @property
    def source_id(self) -> str:
        """Unique identifier for this collector, used in logging and
        downstream routing."""
        return self._config.source_id

    def collect(self) -> list[dict[str, Any]]:
        """
        Load commodity configuration and fetch structured raw market
        data from Yahoo Finance.

        Returns:
            A list of raw record dictionaries, one per symbol per
            timestamp, derived directly from the Yahoo Finance
            response — no normalization or enrichment applied.

        Raises:
            CollectorParseError: If the YAML config is invalid or the
                Yahoo Finance response cannot be parsed.
            CollectorConnectionError: If the Yahoo Finance API cannot
                be reached after all retries are exhausted.
            CollectorTimeoutError: If every retry attempt times out.
        """
        logger.info(f"[{self.source_id}] Starting commodity collection")

        config_filename = self._config.extra.get("commodities_config")
        if not config_filename:
            raise CollectorParseError(
                f"[{self.source_id}] Missing 'commodities_config' entry "
                f"in SourceConfig.extra"
            )

        yaml_path = get_config_path(config_filename)
        parsed_config = load_commodity_config(yaml_path)
        logger.info(f"[{self.source_id}] YAML successfully loaded from '{yaml_path}'")

        categories = parsed_config["commodities"]
        symbols = [
            instrument["symbol"]
            for instruments in categories.values()
            for instrument in instruments
        ]
        interval = parsed_config["settings"]["interval"]
        period = parsed_config["settings"]["period"]

        logger.info(
            f"[{self.source_id}] Loaded {len(symbols)} symbols across "
            f"{len(categories)} categories (interval={interval}, "
            f"period={period})"
        )

        raw_response = self._fetch_with_retries(symbols, interval, period)
        return self._to_raw_records(raw_response, symbols)

    def _fetch_with_retries(
        self, symbols: list[str], interval: str, period: str
    ) -> Any:
        """
        Calls the Yahoo Finance API with exponential-backoff retry and
        timeout handling, following the same retry style as
        GdeltCollector.

        Args:
            symbols: List of ticker symbols to fetch.
            interval: Data interval (e.g. "1d").
            period: Data period (e.g. "5d").

        Returns:
            The raw response object from yfinance (a DataFrame).

        Raises:
            CollectorTimeoutError: If every attempt times out.
            CollectorConnectionError: If every attempt fails to
                connect for a non-timeout reason.
        """
        last_error: Exception | None = None
        max_retries = self._config.max_retries

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    f"[{self.source_id}] API request started "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )
                data = yf.download(
                    tickers=symbols,
                    interval=interval,
                    period=period,
                    group_by="ticker",
                    threads=True,
                    progress=False,
                    timeout=self._config.timeout_seconds,
                )

                if data is None or data.empty:
                    raise CollectorParseError(
                        f"[{self.source_id}] Empty response for symbols: "
                        f"{symbols}"
                    )

                logger.info(
                    f"[{self.source_id}] API request succeeded on "
                    f"attempt {attempt + 1}"
                )
                return data

            except CollectorParseError:
                raise  # bad data shape — retrying won't help

            except TimeoutError as err:
                last_error = err
                logger.warning(
                    f"[{self.source_id}] Timeout on attempt "
                    f"{attempt + 1}: {err}"
                )

            except Exception as err:
                last_error = err
                logger.warning(
                    f"[{self.source_id}] Request failed on attempt "
                    f"{attempt + 1}: {err}"
                )

            if attempt < max_retries:
                backoff = self._retry_backoff_seconds * (2 ** attempt)
                logger.info(f"[{self.source_id}] Retrying in {backoff}s")
                time.sleep(backoff)

        if isinstance(last_error, TimeoutError):
            raise CollectorTimeoutError(
                f"[{self.source_id}] Timed out after {max_retries} "
                f"retries: {last_error}"
            ) from last_error

        raise CollectorConnectionError(
            f"[{self.source_id}] Failed after {max_retries} retries: "
            f"{last_error}"
        ) from last_error

    def _to_raw_records(
        self, data: Any, symbols: list[str]
    ) -> list[dict[str, Any]]:
        """
        Flattens the yfinance DataFrame into a list of raw dictionaries,
        one per symbol per timestamp. Values are passed through as
        returned by Yahoo Finance — no normalization or type coercion
        beyond what's needed to iterate the response.

        Args:
            data: The raw yfinance DataFrame.
            symbols: The list of symbols requested.

        Returns:
            A list of raw record dictionaries.

        Raises:
            CollectorParseError: If the response cannot be iterated
                in the expected shape.
        """
        try:
            records: list[dict[str, Any]] = []
            multi_symbol = len(symbols) > 1

            for symbol in symbols:
                try:
                    symbol_df = data[symbol] if multi_symbol else data
                except KeyError:
                    logger.warning(
                        f"[{self.source_id}] No data returned for "
                        f"symbol '{symbol}', skipping"
                    )
                    continue

                for timestamp, row in symbol_df.iterrows():
                    if row.isnull().all():
                        continue
                    records.append({
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "open": row.get("Open"),
                        "high": row.get("High"),
                        "low": row.get("Low"),
                        "close": row.get("Close"),
                        "volume": row.get("Volume"),
                    })

            logger.info(
                f"[{self.source_id}] Collection successful — "
                f"{len(records)} raw records returned"
            )
            return records

        except Exception as err:
            raise CollectorParseError(
                f"[{self.source_id}] Failed to parse Yahoo Finance "
                f"response: {err}"
            ) from err