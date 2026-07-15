import logging
import traceback

import sys
import os

# Add the src directory (Escr/src) to sys.path to allow importing intelligence_layer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from intelligence_layer.collectors.commodities.Commodity_collector import CommodityCollector
from intelligence_layer.models.source_config import SourceConfig

logging.getLogger("intelligence_layer").setLevel(logging.INFO)

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