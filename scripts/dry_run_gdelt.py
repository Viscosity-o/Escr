import logging
import traceback

from intelligence_layer.collectors.news.gdelt_collector import GdeltCollector
from intelligence_layer.models.source_config import SourceConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

def main():
    config = SourceConfig(
        source_id="gdelt_dry_run",
        timeout_seconds=30,
        max_retries=3,
        extra={
            "filters_config": "gdelt_filters.yaml",
            "retry_backoff_seconds": "5.0",
        },
    )

    collector = GdeltCollector(config)

    try:
        data = collector.collect()
        records = data.get("articles", []) if isinstance(data, dict) else []
        print(f"Total records returned: {len(records)}")
        for record in records[:5]:
            print(record)
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()