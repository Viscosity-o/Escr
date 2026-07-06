# tests/

This directory mirrors the structure of `src/intelligence_layer/` exactly.

Every module in `src/` should have a corresponding test module here.

## Structure

```
tests/
├── collectors/
│   ├── test_base.py
│   ├── news/
│   ├── maritime/
│   ├── sanctions/
│   ├── commodities/
│   ├── conflict/
│   └── weather/
├── validators/
│   └── test_base.py
├── normalizers/
│   └── test_base.py
├── publishers/
│   └── test_base.py
├── models/
│   ├── test_intelligence_record.py
│   └── test_source_config.py
├── utils/
│   ├── test_logging.py
│   ├── test_config_loader.py
│   ├── test_datetime_utils.py
│   └── test_exceptions.py
└── fixtures/          ← Shared test fixtures and sample raw data
```

## Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=intelligence_layer --cov-report=term-missing
```
