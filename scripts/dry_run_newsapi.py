import logging
import time
import traceback
import sys
import os
from dotenv import load_dotenv

# Add the src directory (Escr/src) to sys.path to allow importing intelligence_layer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Load the .env file from the Escr root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

from intelligence_layer.collectors.news.newsapi_collector import NewsApiCollector
from intelligence_layer.collectors.news.newsapi_query_builder import (
    build_newsapi_query_for_group,
    get_filter_group_names,
)
from intelligence_layer.models.source_config import SourceConfig
from intelligence_layer.utils.config_loader import get_config_path

logging.getLogger("intelligence_layer").setLevel(logging.INFO)

INTER_GROUP_DELAY_SECONDS = 7


def main():
    config = SourceConfig(
        source_id="newsapi_dry_run",
        timeout_seconds=30,
        max_retries=3,
        extra={
            "filters_config": "newsapi_filters.yaml",
            "retry_backoff_seconds": "2.0",
            "page_size": "5",
        },
    )

    filters_path = get_config_path("newsapi_filters.yaml")
    # Only test the energy_keywords group as requested
    group_names = ["energy_keywords"]
    print(f"Testing filter group: {group_names}\n")

    for i, group_name in enumerate(group_names):
        print(f"{'='*60}")
        print(f"Testing group: {group_name}")
        print(f"{'='*60}")

        # Build a small query for this group only (max 6 terms)
        query = build_newsapi_query_for_group(filters_path, group_name, max_terms=6)
        print(f"Query: {query}\n")

        # Override the collector's query for this group
        collector = NewsApiCollector(config)
        collector.query = query

        try:
            import json
            data = collector.collect()
            records = data.get("articles", []) if isinstance(data, dict) else []
            total = data.get("totalResults", "?") if isinstance(data, dict) else "?"
            print(f"[OK] {group_name}: {len(records)} articles returned (totalResults={total})\n")
            
            print("--- RAW ARTICLE OBJECTS ---")
            for idx, record in enumerate(records):
                print(f"\nArticle {idx + 1}:")
                print(json.dumps(record, indent=2))
        except Exception:
            print(f"[FAIL] {group_name}: FAILED")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("Dry run complete.")


if __name__ == "__main__":
    main()
