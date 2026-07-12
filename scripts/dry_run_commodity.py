import logging
import traceback

from intelligence_layer.collectors.commodities.Commodity_collector import CommodityCollector
from intelligence_layer.models.source_config import SourceConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

def main():
    config = SourceConfig(
        source_id="commodity_dry_run",
        timeout_seconds=30,
        max_retries=3,
        extra={
            "commodities_config": "yahoo.finance.yaml",
            "retry_backoff_seconds": "5.0",
        },
    )

    collector = CommodityCollector(config)

    try:
        records = collector.collect()
        print(f"Total raw records returned: {len(records)}")
        for record in records[:5]:
            print(record)
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()