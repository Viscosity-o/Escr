# Data Model Reference

## IntelligenceRecord

The canonical output of the Global Intelligence Layer.
Every normalized piece of external intelligence is represented as an `IntelligenceRecord`
before being forwarded downstream.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `record_id` | `str` (UUID) | auto | Unique identifier for this record, auto-generated on creation |
| `source_id` | `str` | yes | Identifier of the collector that produced this record |
| `source_category` | `DataSourceCategory` | yes | High-level category of the originating source |
| `collected_at` | `datetime` (UTC) | yes | When the raw data was fetched |
| `published_at` | `datetime` (UTC) | no | When the item was originally published by the source |
| `title` | `str` | yes | Short summary or headline |
| `content` | `str` | yes | Full or truncated body content |
| `url` | `str` | no | Source URL, if applicable |
| `geo_references` | `list[str]` | no | Geographic entities mentioned (country codes, region names) |
| `tags` | `list[str]` | no | Keywords for routing and filtering |
| `raw_metadata` | `dict[str, Any]` | no | Additional source-specific fields preserved for traceability |

### DataSourceCategory Enum

| Value | Description |
|---|---|
| `news` | News and media intelligence |
| `maritime` | Vessel tracking, port, and shipping data |
| `sanctions` | Sanctions lists and regulatory data |
| `commodities` | Commodity prices and market data |
| `conflict` | Geopolitical conflict and instability events |
| `weather` | Weather and environmental conditions |
| `other` | Catch-all for sources not yet categorized |

---

## SourceConfig

Configuration descriptor for a single external data source.

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `source_id` | `str` | required | Unique identifier matching the collector's source_id |
| `enabled` | `bool` | `True` | Whether this source should be actively collected |
| `poll_interval_seconds` | `int` | `300` | How frequently to collect from this source |
| `timeout_seconds` | `int` | `30` | Max wait time per collection attempt |
| `max_retries` | `int` | `3` | Retry attempts on transient failures |
| `extra` | `dict[str, str]` | `{}` | Additional config — values reference environment variable names |
