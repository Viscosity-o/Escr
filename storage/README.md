# storage/

Local transient storage used during development and for buffering data before publishing.

## Directories

| Directory | Purpose |
|---|---|
| `staging/` | Temporary holding area for raw data between collection and publishing. Cleared after successful publish. |
| `archive/` | Short-term local archive of successfully published records, for debugging and replay. |

## Important Notes

- This directory is for **local/transient use only**.
- In production, staging and archiving should use the appropriate external storage system.
- Contents of `staging/` and `archive/` are excluded from version control via `.gitignore`.
- Only `.gitkeep` files are committed to preserve the directory structure.
