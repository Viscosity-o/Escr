# Global Intelligence Layer

The **Global Intelligence Layer** is the first module of the AI-powered **Energy Supply Chain Resilience** platform.

## Purpose

This module is responsible for continuously gathering external intelligence from multiple public data sources — including news feeds, maritime data, sanctions lists, commodity prices, conflict data, and more — and preparing that raw intelligence for downstream AI processing.

## Scope

This module is responsible **only** for:

- Collecting raw data from external sources
- Validating raw data integrity and structure
- Normalizing data into a consistent internal format
- Publishing/forwarding normalized data to downstream systems

This module is **not** responsible for:

- AI reasoning or inference
- Risk scoring or threat assessment
- Scenario simulation
- Recommendations or alerts
- Dashboard or UI
- RAG (Retrieval-Augmented Generation)
- Knowledge Graph construction
- Machine Learning pipelines

## High-Level Workflow

```
External Data Sources
        ↓
Data Collection Components  (collectors/)
        ↓
Raw Data Validation         (validators/)
        ↓
Data Normalization           (normalizers/)
        ↓
Publish / Forward Downstream (publishers/)
```

## Project Structure

See [docs/architecture.md](docs/architecture.md) for a full explanation of the folder structure and design decisions.

## Getting Started

See [docs/development.md](docs/development.md) for setup and development instructions.
