# F1 Open Lakehouse

A local, open-source lakehouse for Formula 1 data: Apache Iceberg tables on MinIO, written by Spark, read by DuckDB, orchestrated by Airflow, and served through ClickHouse, a REST API and a web UI. It answers what happened, how we know, and what changed afterwards, with every number reproducible.

> **Disclaimer:** Unofficial, non-commercial fan project. Not associated with Formula 1 companies. F1 data comes from Jolpica, OpenF1 and f1db under their own licenses.

## Quick start

Requires WSL2 (keep the repo inside the WSL filesystem, not under `/mnt/c`), Docker Desktop with WSL integration, `make` and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
make check   # location guard, lint, unit tests
make up      # start the stack (added in phase 0, task 2)
make smoke   # Spark writes an Iceberg table, DuckDB reads it (phase 0, task 3)
```

## Docs

- [Project plan](docs/project-plan.md): the spec
- [Roadmap and resume point](docs/ROADMAP.md): current status and how to continue
