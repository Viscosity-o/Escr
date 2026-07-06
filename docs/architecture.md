# Architecture — Global Intelligence Layer

## Overview

The Global Intelligence Layer is a data collection and preparation module.
Its sole responsibility is to gather raw external intelligence and deliver
normalized records to downstream systems.

It does **not** reason about data, score risks, or make recommendations.

---

## Workflow

```
External Data Sources
        │
        ▼
┌─────────────────────┐
│     collectors/     │  Fetch raw data from one external source each
└─────────────────────┘
        │ raw data
        ▼
┌─────────────────────┐
│     validators/     │  Verify raw data structure and integrity
└─────────────────────┘
        │ validated raw data
        ▼
┌─────────────────────┐
│    normalizers/     │  Map to canonical IntelligenceRecord schema
└─────────────────────┘
        │ IntelligenceRecord[]
        ▼
┌─────────────────────┐
│     publishers/     │  Forward to downstream system
└─────────────────────┘
        │
        ▼
  Downstream Systems
  (AI Reasoning, Risk Scoring, etc.)
```

---

## Folder Structure and Design Rationale

```
global-intelligence-layer/
│
├── src/
│   └── intelligence_layer/          # Main Python package
│       │
│       ├── collectors/              # One sub-package per data source category
│       │   ├── base.py              # Abstract BaseCollector interface
│       │   ├── news/                # News & media collectors
│       │   ├── maritime/            # AIS, vessel tracking, port data
│       │   ├── sanctions/           # OFAC, EU, UN sanctions lists
│       │   ├── commodities/         # Oil, gas, LNG price feeds
│       │   ├── conflict/            # Geopolitical conflict event data
│       │   └── weather/             # Weather & environmental alerts
│       │
│       ├── validators/              # Raw data validation (one module per source type)
│       │   └── base.py              # Abstract BaseValidator + ValidationResult
│       │
│       ├── normalizers/             # Data normalization (one module per source type)
│       │   └── base.py              # Abstract BaseNormalizer interface
│       │
│       ├── publishers/              # Downstream forwarding (pluggable implementations)
│       │   └── base.py              # Abstract BasePublisher interface
│       │
│       ├── models/                  # Canonical data models (no ORM)
│       │   ├── intelligence_record.py  # IntelligenceRecord — the core output schema
│       │   └── source_config.py        # SourceConfig — per-source configuration model
│       │
│       └── utils/                   # Shared, stateless utilities
│           ├── logging.py           # Centralized logger factory
│           ├── config_loader.py     # Environment variable and config file access
│           ├── datetime_utils.py    # UTC datetime helpers
│           └── exceptions.py       # Custom exception hierarchy
│
├── config/                          # Static YAML configuration files
│   ├── settings.yaml                # App-wide settings
│   └── sources.yaml                 # Per-source collector configuration
│
├── tests/                           # Mirrors src/ structure exactly
│   ├── collectors/
│   ├── validators/
│   ├── normalizers/
│   ├── publishers/
│   ├── models/
│   ├── utils/
│   └── fixtures/                    # Shared sample data and pytest fixtures
│
├── storage/                         # Local transient storage (excluded from VCS)
│   ├── staging/                     # In-progress records awaiting publish
│   └── archive/                     # Short-term local record of published data
│
├── scripts/                         # Operational utility scripts
│   ├── validate_config.py
│   └── check_sources.py
│
└── docs/                            # Project documentation
    ├── architecture.md              # This file
    ├── development.md               # Dev setup and workflow
    ├── adding_a_new_source.md       # Step-by-step guide for new collectors
    └── data_model.md                # IntelligenceRecord schema reference
```

---

## Key Design Decisions

**Strict layer separation**
Each layer (collect → validate → normalize → publish) has a single responsibility.
No layer skips or merges with another. This makes each layer independently testable
and replaceable.

**Abstract base classes everywhere**
Every layer defines an abstract base class. Concrete implementations must conform
to the contract. This enforces consistency and makes it trivial to add new sources
or swap out publishers without touching other code.

**Technology-agnostic**
No specific message queue, database, HTTP library, or serialization format is
assumed. These are configuration and implementation decisions, not architectural ones.

**Canonical data model**
All normalized output is an `IntelligenceRecord`. Downstream systems receive
a consistent schema regardless of which source produced the data.

**Config over code**
New sources are enabled/disabled in `config/sources.yaml`, not by changing code.
Credentials never appear in config files — they are always environment variables.

**Mirrors test structure**
`tests/` mirrors `src/` so every module has a natural home for its tests,
making coverage gaps immediately obvious.
