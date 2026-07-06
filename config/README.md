# config/

This directory holds all static configuration files for the Global Intelligence Layer.

## What goes here

| File | Purpose |
|---|---|
| `settings.yaml` | General application settings (log level, intervals, feature flags) |
| `sources.yaml` | Per-source configuration: enabled/disabled, poll intervals, timeouts |
| `publisher.yaml` | Configuration for the downstream publish target |
| `logging.yaml` | Logging handler and formatter configuration (optional override) |

## What does NOT go here

- Secrets (API keys, passwords, tokens) — use environment variables via `.env`
- Environment-specific overrides — use `.env` per environment
- Dynamic runtime state — use `storage/`

## How configuration is read

All configuration access goes through `src/intelligence_layer/utils/config_loader.py`.
No component should read config files or environment variables directly.
