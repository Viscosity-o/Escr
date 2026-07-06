# scripts/

Operational and utility scripts for developers and operators.

These are standalone scripts for tasks that are **not** part of the main application runtime.

## Intended Scripts

| Script | Purpose |
|---|---|
| `run_collector.py` | Manually trigger a single collector by source_id (useful for debugging) |
| `validate_config.py` | Parse and validate all config files, report any issues |
| `check_sources.py` | Ping all enabled data sources and report connectivity status |
| `replay_staging.py` | Re-publish records currently sitting in `storage/staging/` |
| `clear_staging.py` | Safely clear the staging directory after confirming records are published |

## Rules

- Scripts are for **operational use only** — no business logic lives here.
- All scripts import from `src/intelligence_layer/` rather than duplicating code.
- Scripts should be runnable from the project root: `python scripts/<script_name>.py`
