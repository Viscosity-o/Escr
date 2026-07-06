# Adding a New Data Source

Follow these steps every time a new external data source is introduced.

---

## Step 1 — Create the collector sub-package

Add a new module inside the appropriate category under `collectors/`.
If the category does not exist, add a new sub-package.

```
src/intelligence_layer/collectors/<category>/<source_name>.py
```

The collector class must extend `BaseCollector` and implement:
- `source_id` property — a unique, stable string identifier
- `collect()` method — fetches and returns raw data, no transformation

---

## Step 2 — Add a validator

Create a corresponding validator in `validators/`:

```
src/intelligence_layer/validators/<source_name>.py
```

Extend `BaseValidator` and implement `validate(raw_data)` returning a `ValidationResult`.

---

## Step 3 — Add a normalizer

Create a corresponding normalizer in `normalizers/`:

```
src/intelligence_layer/normalizers/<source_name>.py
```

Extend `BaseNormalizer` and implement `normalize(raw_data)` returning `list[IntelligenceRecord]`.

---

## Step 4 — Register the source in config

Add an entry to `config/sources.yaml`:

```yaml
- source_id: your_new_source_id
  category: <category>
  enabled: true
  poll_interval_seconds: 300
  timeout_seconds: 30
  max_retries: 3
  extra:
    api_key_env: YOUR_NEW_SOURCE_API_KEY
```

---

## Step 5 — Add environment variable placeholder

Add the secret key to `.env.example`:

```bash
# YOUR_NEW_SOURCE_API_KEY=
```

---

## Step 6 — Write tests

Add test modules mirroring the new files:

```
tests/collectors/<category>/test_<source_name>.py
tests/validators/test_<source_name>.py
tests/normalizers/test_<source_name>.py
```

Add sample raw data to `tests/fixtures/raw/`.

---

## Checklist

- [ ] Collector class created and extends `BaseCollector`
- [ ] Validator created and extends `BaseValidator`
- [ ] Normalizer created and extends `BaseNormalizer`
- [ ] Source entry added to `config/sources.yaml`
- [ ] Environment variable placeholder added to `.env.example`
- [ ] Tests written for all three components
- [ ] Sample fixture data added to `tests/fixtures/raw/`
