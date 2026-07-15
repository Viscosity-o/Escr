import logging
import time
import traceback
import sys
import os
# Add the src directory (Escr/src) to sys.path to allow importing intelligence_layer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from intelligence_layer.collectors.news.gdelt_collector import GdeltCollector
from intelligence_layer.collectors.news.query_builder import (
    build_query_for_group,
    get_filter_group_names,
)
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.config_loader import get_config_path

logging.getLogger("intelligence_layer").setLevel(logging.INFO)

INTER_GROUP_DELAY_SECONDS = 7


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

    filters_path = get_config_path("gdelt_filters.yaml")
    group_names = get_filter_group_names(filters_path)
    print(f"Found {len(group_names)} filter groups: {group_names}\n")

    for i, group_name in enumerate(group_names):
        print(f"{'='*60}")
        print(f"[{i+1}/{len(group_names)}] Testing group: {group_name}")
        print(f"{'='*60}")

        # Build a small query for this group only (max 6 terms)
        query = build_query_for_group(filters_path, group_name, max_terms=6)
        print(f"Query: {query}\n")

        # Override the collector's query for this group
        collector = GdeltCollector(config)
        collector.query = query

        try:
            data = collector.collect()
            records = data.get("articles", []) if isinstance(data, dict) else []
            print(f"[OK] {group_name}: {len(records)} articles returned")
            for record in records[:3]:
                title = record.get("title", "N/A") if isinstance(record, dict) else record
                print(f"  - {title}")
        except Exception:
            print(f"[FAIL] {group_name}: FAILED")
            traceback.print_exc()

        # Delay between groups to respect GDELT rate limits
        if i < len(group_names) - 1:
            print(f"\nWaiting {INTER_GROUP_DELAY_SECONDS}s before next group...\n")
            time.sleep(INTER_GROUP_DELAY_SECONDS)

    print(f"\n{'='*60}")
    print("Dry run complete.")


if __name__ == "__main__":
    main()