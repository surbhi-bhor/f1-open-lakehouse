# F1 Open Lakehouse — Roadmap and Resume Point

This file is the single source of truth for "where am I". Update the **Resume here** block at the end of every work session and in every task commit.

Spec: [`docs/project-plan.md`](project-plan.md) (moved from the repo root in phase 0, task 1).

## Resume here

| Field | Value |
| --- | --- |
| Current phase | 0 Foundation |
| Current plan | `docs/superpowers/plans/2026-10-30-phase-0-foundation.md` |
| Current task | Tasks 0 to 3 done (2026-11-07: Spark writes, DuckDB reads `lake.bronze.smoke_drivers`). Task 4 not started |
| Last green commit | Task 3 commit ("Spark writes and DuckDB reads the same Iceberg table"). `make check` 11 passed; `make test-int` 3 passed; `make smoke` prints the three rows |
| Blockers | Memory: close Chrome and Brave and stop the content pipeline before `make up` or Spark jobs |
| Next action | Task 4, step 1 (measure memory) |

Storage: MinIO's official images and binaries are gone (Docker Hub 404, dl.min.io 410). It is built from official source by `.github/workflows/minio-image.yml` on a GitHub runner, because building it on this laptop ran Windows out of memory and crashed WSL. S3 is at `http://localhost:9000`, and the console at `http://localhost:9001`.

Memory: this laptop's commit limit (RAM plus page file, about 30 GB) runs out when browsers hold 5 GB or more. Close Chrome and Brave before `make up` or Spark jobs. Lasting fix: raise the page file (`sysdm.cpl`, custom size 16384 to 24576 MB).

Known issue: on 2026-10-30, Docker Desktop's engine crashed (`wsl.exe -d docker-desktop` exit `0xc00000fd`) after about 50 minutes, and choosing "Quit" in the recovery dialog closed Docker. Fix: `wsl --shutdown`, then reopen Docker Desktop. If it keeps happening, run `wsl --update` and pick "Restart" in that dialog, not "Quit". Docker server 29.9.2, WSL 2.7.11.

Repo location: this Windows folder, `C:\Users\surbh\Documents\Project work\Data engineering\f1-open-lakehouse`. It is the only working copy (the user's decision on 2026-10-30). Run commands from Ubuntu: open Ubuntu, then `cd "/mnt/c/Users/surbh/Documents/Project work/Data engineering/f1-open-lakehouse"`. The Python venv lives in `~/.venvs/f1lake` inside Ubuntu.

## How to resume after an interruption

Run these in order, from the Ubuntu (WSL) shell in the repo folder (path above):

1. `git status` and `git log --oneline -5`. Uncommitted changes belong to the task named above; finish or discard them before anything else.
2. Read the **Resume here** block above, then open the current plan and find the first unticked `- [ ]` step.
3. `make check` confirms the repo is sane (lint and unit tests; compose config from task 2). From task 2 on, `make up` and then `make smoke` also confirm the stack and lake still work.
4. Continue at the first unticked step. Each task is self-contained and ends in its own commit, so a half-done task is redone from its step 1. Every script in this repo is safe to re-run.
5. If you are resuming with Claude Code: start it in this Windows folder and say "resume from docs/ROADMAP.md". For a long break, `/context-save` before stopping and `/context-restore` after.

**Rules that keep resuming cheap:**
- One commit per task, and that commit also ticks the plan's checkboxes and updates the block above.
- Never leave `main` red. Work in progress that cannot be finished goes on a `wip/<task>` branch.
- Measured numbers (memory, timings) go into `docs/benchmarks/` the moment they are measured, never only into chat.

## Phase status

Every phase ends with a gate. Do not start the next phase until its gate passes. The plan for each phase is written only when the previous gate has passed, so it can use what was learned.

| Phase | Status | Plan file | Exit gate (from the spec) |
| --- | --- | --- | --- |
| 0 Foundation | not started | `plans/2026-10-30-phase-0-foundation.md` | One Iceberg table written by Spark and read by DuckDB; memory measured with docker stats; CI green |
| 1 Batch backfill, dimensions | not planned | to write after gate 0 | Several seasons in bronze through an Airflow backfill; SCD2 dims; versioned fact_race_result; dbt tests pass; one time-travel query on a corrected result |
| 2 Streaming | not planned | to write after gate 1 | Recorded session replayed into Redpanda; Structured Streaming writes fact_lap, fact_position, fact_race_control_event with a watermark; small files visible |
| 3 Maintenance, multi-engine | not planned | to write after gate 2 | f1_table_maintenance DAG; partition evolution; DuckDB reads; benchmark report; catalog swapped to Polaris or Lakekeeper if stable |
| 4 Serving API and UI | not planned | to write after gate 3 | gold published to ClickHouse with a parity check; FastAPI endpoints; React UI with five pages including the time-travel view |
| 5 Quality and lineage | not planned | to write after gate 4 | dbt tests and contracts; freshness checks; lineage in Marquez or dbt docs; one documented caught failure |
| 6 Demo and polish | not planned | to write after gate 5 | Static demo hosted; README, case study, ADRs; fresh-clone test passes |
| 7 ML-ready hooks (optional) | not planned | optional | Feature and label tables with a leakage test; empty prediction schema; API stub |
| 8 Databricks leg (optional) | not planned | optional, after phase 3 | Egress test run; one mart rebuilt on Delta; open vs managed ADR |

The core is phases 0 to 4. Phases 7 and 8, plus Marquez, Superset and Trino, are stretch goals.

## Phase 1 sketch (turn into a full plan after gate 0)

Recorded here so the thinking survives an interruption. It is not a plan yet.

1. Source spike: confirm the Jolpica, OpenF1 and f1db endpoints, rate limits and licenses. Write the result into `docs/sources.md`. The spec lists these as from memory and unverified.
2. A cached API client (landing zone: one immutable JSON file per request in the MinIO `landing` bucket), validated with Pydantic.
3. Airflow on LocalExecutor in the `batch` profile, sharing the existing Postgres instance (a separate `airflow` database).
4. `f1_batch_backfill` with one mapped task per season, plus a shared pool for the API rate limit.
5. Bronze tables (append-only, with `ingested_at`), then profile the real data before freezing silver and gold columns.
6. Conformed dims with SCD2 (constructor, circuit, driver assignments), plus the `-1` unknown member and inferred members.
7. `fact_race_result` (versioned) and `fact_qualifying_result`; dbt tests; the time-travel query on a corrected result.

## Machine facts (measured 2026-10-30)

| Item | Value |
| --- | --- |
| RAM | 15.8 GB, so the "16 GB: full, in groups" profile applies |
| CPU | i7-1195G7, 8 logical processors |
| Disk | C: 97.9 GB free (use only C:) |
| WSL | Ubuntu (WSL2) and docker-desktop installed |
| `.wslconfig` | was `memory=12GB`; phase 0, task 0 lowers it to 10GB |
| Shared Docker engine | The Personal Content Intelligence Pipeline (Postgres 5432, Dagster 3000, Metabase 4000, Flask 5000, Ollama 11434) uses the same Docker engine and the same 10 GB. Stop it before `make up`. F1's Postgres is published on 5433 |

## Skills to use, by kind of work

| When | Skill |
| --- | --- |
| Executing a plan, task by task | `superpowers:executing-plans` or `superpowers:subagent-driven-development` |
| Writing any code | `superpowers:test-driven-development` |
| Something fails | `superpowers:systematic-debugging` |
| Before claiming a task or gate is done | `superpowers:verification-before-completion` |
| Writing the next phase's plan | `superpowers:brainstorming` on anything still open, then `superpowers:writing-plans`, then `plan-eng-review` |
| Pinning tool versions and config keys (Iceberg, Spark, Airflow, ClickHouse) | context7 docs lookup. Never trust remembered versions |
| CI workflows | `agent-skills:ci-cd-and-automation` |
| ADRs and the README | `agent-skills:documentation-and-adrs`, `document-generate` |
| Architecture diagrams | `diagram` |
| Before merging each phase | `review` or `/code-review`, plus `security-review` for anything touching credentials |
| Phase 4 UI | `frontend-design:frontend-design`, `impeccable`, `dataviz` |
| Pausing and resuming | `context-save`, `context-restore` |
