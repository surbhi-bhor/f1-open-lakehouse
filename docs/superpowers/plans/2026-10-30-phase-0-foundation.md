# Phase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the riskiest piece first. One command starts MinIO, a JDBC Iceberg catalog on Postgres, and Spark. Spark writes one Iceberg table, DuckDB reads the same table, memory is measured, and CI is green.

**Architecture:** Docker Compose on WSL2 runs MinIO (S3 storage, `warehouse` and `landing` buckets), Postgres (the Iceberg JDBC catalog only; it never holds F1 data) and an idle Spark container that jobs run in through `spark-submit`. Connection settings live in one Python module, `f1lake.config`, used by both the Spark job and the DuckDB reader, so the two engines cannot drift apart. DuckDB runs on the WSL host, finds the table's current metadata file through the catalog, and reads it with `iceberg_scan`.

**Tech Stack:** Docker Compose, MinIO, Postgres 16, Apache Spark 3.5 (Scala 2.12) with the Iceberg Spark runtime, DuckDB (iceberg and httpfs extensions), Python 3.12 managed by uv, pytest, ruff, GitHub Actions.

**Spec:** `docs/project-plan.md` (sections: Tech stack, Phase plan row 0, Laptop and environment, Risks). Resume state lives in `docs/ROADMAP.md`.

## Global Constraints

- Everything is free and open source. No cloud accounts.
- One command starts the environment: `make up`.
- The repo lives in the Windows folder `C:\Users\surbh\Documents\Project work\Data engineering\f1-open-lakehouse` (the user's decision, overriding the spec's "keep it inside WSL"). Commands (`make`, `uv`, `docker`) run from Ubuntu (WSL2) in `/mnt/c/Users/surbh/Documents/Project work/Data engineering/f1-open-lakehouse`. The uv venv lives outside the folder in `~/.venvs/f1lake`, because a Linux venv inside a Windows folder breaks. Lake data stays in Docker named volumes, so only code reads pay the `/mnt/c` slowdown.
- Text files are LF (`.gitattributes`), so bash scripts still run in Linux containers if Windows git touches them.
- The 16 GB profile applies: Compose profiles (`batch`, `streaming`, `serving`) start in groups, never all together. Phase 0 only uses `batch`.
- Every Compose service has a `mem_limit`. Phase 0 total budget: about 4.5 GB (MinIO 512m, Postgres 512m, Spark 3g).
- Phase 0 uses a JDBC catalog. The swap to Polaris or Lakekeeper is phase 3.
- Never use a `latest` image tag. Pin every image and Maven package version in `.env.example`.
- Version pins below are a starting point from memory. Before pinning, confirm each one exists (context7 or Docker Hub/Maven Central): Spark `3.5.6`, Iceberg `1.9.2` (`iceberg-spark-runtime-3.5_2.12`, `iceberg-aws-bundle`), Postgres JDBC `42.7.4`, `postgres:16`.
- **Ruling (2026-11-02): MinIO is built from official source, on GitHub.** MinIO Inc. withdrew its images (Docker Hub 404) and binaries (dl.min.io 410). The user chose MinIO over the SeaweedFS fallback, and chose official source over the `pgsty` fork and `bitnamilegacy`. `infra/minio/Dockerfile` builds MinIO `RELEASE.2025-10-15T17-29-55Z` and mc `RELEASE.2025-08-13T08-35-41Z`, and the build checks each commit SHA. Building on the laptop exhausted Windows memory and crashed WSL, so `.github/workflows/minio-image.yml` builds on a GitHub runner and publishes `ghcr.io/surbhi-bhor/f1lake-minio:<release>`, and the laptop only pulls it. Credentials are `S3_ACCESS_KEY` and `S3_SECRET_KEY` (mapped to `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`). Verified pins: Spark `3.5.7-java17-python3` (Ruling 2026-11-07: Iceberg 1.12 needs Java 17, and the plain `-python3` tag ships Java 11 and Python 3.8), Iceberg `1.12.0`, Postgres JDBC `42.7.14`, `postgres:16.15`.
- Python dependencies only through uv (`pyproject.toml` and `uv.lock`).
- Credentials only in `.env`, which git ignores. `.env.example` holds safe local defaults.
- The README carries the unofficial, non-commercial fan-project disclaimer from day one.
- No number goes into a doc or the resume unless it was measured; it is recorded in `docs/benchmarks/`.

## Review Focus

1. **Re-running a load must not duplicate rows** (spec design rule). Task 3 test `test_rewrite_is_idempotent`.
2. **Restarting the stack keeps the data, and the bucket init is safe to re-run.** `make down && make up` must not lose the table or fail on existing buckets. Task 3 test `test_survives_restart`, plus `--ignore-existing` in Task 2.
3. **A service without a memory cap can starve WSL and freeze the laptop.** Task 2 test `test_every_service_has_mem_limit`.
4. **A missing secret must fail loudly, not connect with an empty password.** Task 1 test `test_load_settings_missing_secret_raises`.
5. **Windows CRLF line endings break bash scripts and Makefiles in Linux.** `.gitattributes` forces LF, and the test `test_gitattributes_forces_lf` pins it (added after Task 1, when the repo moved back to the Windows folder; the location guard was removed then).

---

### Task 0: Environment prep (manual, no code)

**Files:** none in the repo. Edits `C:\Users\surbh\.wslconfig`.

- [x] **Step 1: Lower the WSL memory cap.** Set `C:\Users\surbh\.wslconfig` to:
```ini
[wsl2]
memory=10GB
processors=6
swap=4GB
```
Then in PowerShell run `wsl --shutdown`.
Reason: with 15.8 GB of RAM, a 12 GB cap leaves Windows about 4 GB, and Chrome plus VS Code alone used about 6 GB when measured.

- [x] **Step 2: Start Docker Desktop.** In Settings, then Resources, then WSL integration, enable **Ubuntu**.
Verify, in the Ubuntu shell: `docker run --rm hello-world` prints "Hello from Docker!".

- [x] **Step 3: Move the repo into WSL.** In Ubuntu:
```bash
cp -r "/mnt/c/Users/surbh/Documents/Project work/Data engineering/f1-open-lakehouse" ~/f1-open-lakehouse
cd ~/f1-open-lakehouse && git status
```
Expected: the same untracked files as on Windows. Keep the Windows copy until Task 1 is committed, then delete it, so there is only one working copy.
Superseded on 2026-10-30: the user chose to keep the repo in the Windows folder. The Task 1 commit was pulled back there, and the WSL copy is no longer used.

- [x] **Step 4: Install the tooling in Ubuntu.**
```bash
sudo apt-get update && sudo apt-get install -y make git
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
```
Verify: `make --version`, `uv --version`, and `uv python find 3.12` all succeed.

- [x] **Step 5: Record it.** Update the **Resume here** block in `docs/ROADMAP.md` (current task: Task 1). No commit yet, because the first commit is Task 1.

---

### Task 1: Repo skeleton, settings module, location guard

**Files:**
- Move: `docs/F1 Open Lakehouse Project Plan.md` to `docs/project-plan.md` (`git mv` after the first add)
- Create: `.gitignore`, `.env.example`, `pyproject.toml`, `Makefile`, `README.md`
- Create: `src/f1lake/__init__.py` (empty), `src/f1lake/config.py`
- Create: `scripts/guard_location.sh`
- Test: `tests/unit/test_config.py`, `tests/unit/test_guard.py`

**Interfaces:**
- Produces, in `f1lake.config`:
  - `@dataclass(frozen=True) class Settings` with fields `s3_endpoint: str`, `s3_access_key: str`, `s3_secret_key: str`, `pg_host: str`, `pg_port: int`, `pg_user: str`, `pg_password: str`, `pg_catalog_db: str = "iceberg_catalog"`, `warehouse: str = "s3://warehouse/"`, `catalog_name: str = "lake"`
  - `load_settings(env: Mapping[str, str] = os.environ) -> Settings`
  - `spark_catalog_conf(s: Settings) -> dict[str, str]`
- Environment variables read by `load_settings`, with defaults: `S3_ENDPOINT` (`http://localhost:9000`), `MINIO_ROOT_USER` (required), `MINIO_ROOT_PASSWORD` (required), `PG_HOST` (`localhost`), `PG_PORT` (`5433`; host port, because the content-intelligence pipeline already holds 5432), `POSTGRES_USER` (required), `POSTGRES_PASSWORD` (required).
- Make targets: `guard`, `lint`, `test`, `check` (`check` = guard + lint + test; Task 2 adds compose validation).

- [x] **Step 1: Write the failing tests** in `tests/unit/test_config.py`:

```python
ENV = {"MINIO_ROOT_USER": "u", "MINIO_ROOT_PASSWORD": "p",
       "POSTGRES_USER": "pg", "POSTGRES_PASSWORD": "pgp", "PG_HOST": "postgres",
       "PG_PORT": "5432", "S3_ENDPOINT": "http://minio:9000"}

def test_spark_conf_uses_jdbc_catalog():
    conf = spark_catalog_conf(load_settings(ENV))
    p = "spark.sql.catalog.lake"
    assert conf[p] == "org.apache.iceberg.spark.SparkCatalog"
    assert conf[f"{p}.catalog-impl"] == "org.apache.iceberg.jdbc.JdbcCatalog"
    assert conf[f"{p}.uri"] == "jdbc:postgresql://postgres:5432/iceberg_catalog"
    assert conf[f"{p}.warehouse"] == "s3://warehouse/"
    assert conf[f"{p}.io-impl"] == "org.apache.iceberg.aws.s3.S3FileIO"
    assert conf[f"{p}.s3.endpoint"] == "http://minio:9000"
    assert conf[f"{p}.s3.path-style-access"] == "true"
    assert conf["spark.sql.extensions"] == "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"

def test_defaults_target_localhost():
    s = load_settings({k: v for k, v in ENV.items() if k not in ("PG_HOST", "PG_PORT", "S3_ENDPOINT")})
    assert (s.pg_host, s.pg_port, s.s3_endpoint) == ("localhost", 5433, "http://localhost:9000")

def test_load_settings_missing_secret_raises():
    env = dict(ENV); del env["MINIO_ROOT_PASSWORD"]
    with pytest.raises(KeyError, match="MINIO_ROOT_PASSWORD"):
        load_settings(env)
```

`tests/unit/test_guard.py` runs `scripts/guard_location.sh <dir>` through `subprocess`:
- `test_guard_rejects_mnt_c`: `/mnt/c/x` gives exit code 1, and stderr contains `inside the WSL filesystem`.
- `test_guard_accepts_home`: `/home/u/f1-open-lakehouse` gives exit code 0.

- [x] **Step 2: Run them and see them fail.**
Run: `uv run pytest tests/unit -v`
Expected: FAIL (ImportError for `f1lake.config`, and the guard script is missing).

- [x] **Step 3: Write `pyproject.toml`.** Package `f1lake`, src layout, `requires-python = ">=3.12"`. Dependencies: `duckdb`, `psycopg[binary]`. Dev group: `pytest`, `ruff`, `pyyaml`. Add a pytest marker `integration` and `addopts = "-m 'not integration'"`. Run `uv sync`, which creates `uv.lock`.

- [x] **Step 4: Implement `f1lake/config.py`.** A required variable missing from `env` raises `KeyError` naming the variable (plain `env["X"]` does this). Also set `client.region` to `us-east-1`; S3FileIO needs a region even for MinIO. In Spark, the S3 credentials come from `s3.access-key-id` and `s3.secret-access-key` on the catalog.

- [x] **Step 5: Implement `scripts/guard_location.sh <dir>`.** It exits 1 with the message `repo must live inside the WSL filesystem (~/...), not under /mnt/` when `<dir>` starts with `/mnt/`, and exits 0 otherwise. The Makefile's `guard` target calls it with `$(CURDIR)`.

- [x] **Step 6: Write the remaining skeleton.**
  - `.gitignore`: `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `graphify-out/`
  - `.env.example`: the variables above, with local-only values such as `MINIO_ROOT_USER=f1admin`
  - `README.md`: a one-paragraph purpose, Quick start (`cp .env.example .env`, `make up`, `make smoke`), and the disclaimer: *"Unofficial, non-commercial fan project. Not associated with Formula 1 companies. F1 data comes from Jolpica, OpenF1 and f1db under their own licenses."*
  - `Makefile`: `guard`, `lint` (`uv run ruff check .`), `test` (`uv run pytest`), `check`

- [x] **Step 7: Run the checks and see them pass.**
Run: `make check`
Expected: the guard passes, ruff is clean, and 5 tests pass.

- [x] **Step 8: Commit.** Tick this task's boxes and update the Resume block first.
```bash
git add -A && git mv "docs/F1 Open Lakehouse Project Plan.md" docs/project-plan.md
git commit -m "chore: repo skeleton, settings module and WSL location guard"
```

---

### Task 2: Compose stack (MinIO, catalog Postgres, Spark)

**Files:**
- Create: `docker-compose.yml`, `infra/postgres/init.sql`
- Modify: `.env.example` (image and package pins), `Makefile` (`up`, `down`, `ps`, `stats`; add `compose-config` to `check`)
- Test: `tests/unit/test_compose.py`

**Interfaces:**
- Consumes: the environment variable names from Task 1.
- Produces:
  - Services `minio` (ports 9000 and 9001), `minio-init` (one-shot), `postgres` (published as `127.0.0.1:5433:5432`, so it can coexist with the content-intelligence pipeline's 5432; databases `iceberg_catalog`, plus `airflow` reserved for phase 1), `spark` (profiles `batch` and `streaming`; repo mounted at `/opt/project`; `PYTHONPATH=/opt/project/src`; `PG_HOST=postgres`; `PG_PORT=5432`; `S3_ENDPOINT=http://minio:9000`; a named volume for the Ivy jar cache at `/opt/ivy`)
  - Buckets `warehouse` and `landing`
  - The Make variable `SPARK_SUBMIT`, which is `docker compose exec spark /opt/spark/bin/spark-submit --master local[2] --driver-memory 2g --conf spark.jars.ivy=/opt/ivy --packages $(ICEBERG_PACKAGES)`. Task 3 uses it.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_compose.py`. They load `docker-compose.yml` with pyyaml.
  - `test_every_service_has_mem_limit`: every service has a `mem_limit` key.
  - `test_no_image_uses_latest_tag`: no `image` value ends in `:latest` or has no tag. A `${VAR}` reference counts as pinned, and the test asserts that `VAR` is present in `.env.example`.
  - `test_spark_only_in_profiles`: the `spark` service has `profiles` equal to `["batch", "streaming"]`, and `minio` and `postgres` have no profiles.
  - `test_env_file_is_gitignored`: `.env` is a line in `.gitignore`.

- [x] **Step 2: Run them and see them fail.** Run `uv run pytest tests/unit/test_compose.py -v`. Expected: FAIL, because the file is missing.

- [x] **Step 3: Pin the versions.** Confirm each tag and version exists (Global Constraints), then add `SPARK_IMAGE`, `MINIO_IMAGE`, `MC_IMAGE`, `POSTGRES_IMAGE`, `ICEBERG_VERSION` and `PG_JDBC_VERSION` to `.env.example`.

- [x] **Step 4: Write `docker-compose.yml` and `infra/postgres/init.sql`.**
  - `minio`: `server /data --console-address :9001`, a named volume, healthcheck `mc ready local`, `mem_limit: 512m`.
  - `minio-init`: depends on `minio` being healthy; runs `mc alias set` and then `mc mb --ignore-existing local/warehouse local/landing`. `--ignore-existing` is what makes a restart safe (Review Focus 2).
  - `postgres`: a named volume, `init.sql` mounted into `/docker-entrypoint-initdb.d/`, healthcheck `pg_isready`, `mem_limit: 512m`. `init.sql` runs `CREATE DATABASE iceberg_catalog;` and `CREATE DATABASE airflow;`.
  - `spark`: runs `sleep infinity` and `mem_limit: 3g`. Add the comment `# shortcut: local[2] in one container, no standalone master/worker; upgrade when streaming and batch must run together`.

- [x] **Step 5: Add the Make targets.**
  - `up`: `docker compose --profile batch up -d --wait`
  - `down`: `docker compose --profile batch down` (keeps volumes)
  - `ps`
  - `stats`: `docker stats --no-stream`
  - `compose-config`: `docker compose --profile batch config -q`, and `check` now includes it

- [x] **Step 6: Run the tests and bring the stack up.**
Run: `make check && cp -n .env.example .env && make up && make ps`
Expected: tests pass; `minio` and `postgres` are healthy, `spark` is running, and `minio-init` has exited 0. Open http://localhost:9001 and you see both buckets.
Run `make down && make up` a second time. Expected: it succeeds again.

- [x] **Step 7: Commit.**
```bash
git add -A && git commit -m "feat: compose stack with MinIO, JDBC catalog Postgres and Spark"
```

---

### Task 3: Write with Spark, read with DuckDB (the phase 0 proof)

**Files:**
- Create: `jobs/smoke_write.py`, `src/f1lake/read_duckdb.py`
- Modify: `Makefile` (`smoke-write`, `smoke-read`, `smoke`, `test-int`)
- Test: `tests/integration/test_iceberg_roundtrip.py`

**Interfaces:**
- Consumes: `load_settings` and `spark_catalog_conf` (Task 1); `SPARK_SUBMIT` and the running stack (Task 2).
- Produces:
  - Table `lake.bronze.smoke_drivers`: `driver_id STRING`, `code STRING`, `season INT`, `ingested_at TIMESTAMP`, `PARTITIONED BY (season)`.
  - `f1lake.read_duckdb.metadata_location(s: Settings, namespace: str, table: str) -> str`
  - `f1lake.read_duckdb.read_table(s: Settings, namespace: str, table: str, columns: list[str]) -> list[tuple]`. Rows come back ordered by the first column.

- [x] **Step 1: Write the failing tests** in `tests/integration/test_iceberg_roundtrip.py`. Mark them `pytest.mark.integration`. A helper `write()` runs `make smoke-write` through `subprocess.run(check=True)`.

```python
EXPECTED = [("hamilton", "HAM", 2024), ("leclerc", "LEC", 2024), ("max_verstappen", "VER", 2024)]
COLS = ["driver_id", "code", "season"]

def test_roundtrip_spark_write_duckdb_read():
    write()
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED

def test_rewrite_is_idempotent():
    write(); write()
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED

def test_survives_restart():
    write()
    subprocess.run(["make", "down"], check=True); subprocess.run(["make", "up"], check=True)
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED
```

On the host, `load_settings()` reads `.env`. Load it in `tests/integration/conftest.py` with a ten-line `KEY=VALUE` parser, not python-dotenv.

- [x] **Step 2: Run them and see them fail.** Run `uv run pytest -m integration -v`. Expected: FAIL, because `make smoke-write` and `f1lake.read_duckdb` are missing.

- [x] **Step 3: Implement `jobs/smoke_write.py`.**
  - Build the SparkSession from `spark_catalog_conf(load_settings())`.
  - Run `CREATE NAMESPACE IF NOT EXISTS lake.bronze` and `CREATE TABLE IF NOT EXISTS` with the schema above.
  - Write the three EXPECTED rows with `ingested_at = current_timestamp()` using `df.writeTo("lake.bronze.smoke_drivers").overwritePartitions()`. Overwriting the whole partition is what makes the re-run idempotent, which is the spec's "overwrite a whole partition" rule.
  - Print the snapshot count from `lake.bronze.smoke_drivers.snapshots`. It grows each run, and that is the first time-travel evidence.

  Make target `smoke-write`: `$(SPARK_SUBMIT) /opt/project/jobs/smoke_write.py`.

- [x] **Step 4: Implement `f1lake/read_duckdb.py`.**
  - `metadata_location` runs `SELECT metadata_location FROM iceberg_tables WHERE catalog_name = %s AND table_namespace = %s AND table_name = %s` against `iceberg_catalog` with psycopg. It raises `LookupError` naming the table when there is no row. Add the comment `# shortcut: reads the JDBC catalog table directly; replace with a REST catalog client when moving to Polaris/Lakekeeper in phase 3`.
  - `read_table` does three things in order:
    1. Runs `INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs`.
    2. Creates `CREATE SECRET (TYPE s3, KEY_ID ?, SECRET ?, ENDPOINT '<host:port without scheme>', URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')`.
    3. Runs `SELECT <columns> FROM iceberg_scan(?) ORDER BY 1`, with the column names checked against `^[a-z_]+$` before they are interpolated.

  Make targets: `smoke-read` (`uv run python -m f1lake.read_duckdb`, whose `__main__` prints the rows), `smoke` (smoke-write then smoke-read), and `test-int` (`uv run pytest -m integration`).

- [x] **Step 5: Run the tests and see them pass.**
Run: `make up && make test-int`
Expected: 3 passed. The first run downloads the Iceberg jars into the Ivy volume, which is slow once and then cached.
If DuckDB's `iceberg_scan` rejects the metadata, check the version-hint behaviour of the DuckDB version in use with context7 before changing any code (`superpowers:systematic-debugging`).

- [x] **Step 6: Commit.**
```bash
git add -A && git commit -m "feat: Spark writes and DuckDB reads the same Iceberg table"
```

---

### Task 4: Measure memory, CI skeleton, close the gate

**Files:**
- Create: `docs/benchmarks/phase0-memory.md`, `.github/workflows/ci.yml`
- Modify: `docs/ROADMAP.md` (phase 0 done, Resume block set to phase 1)

**Interfaces:**
- Consumes: the Make targets `check`, `up`, `test-int` and `down`.

- [x] **Step 1: Measure memory.** Run `make up`, then `make stats` three times: idle, during `make smoke-write` (from a second shell), and right after it. Record each service's MEM USAGE and the machine's free RAM (`free -h` in WSL) in `docs/benchmarks/phase0-memory.md`, along with the date, the machine facts from the ROADMAP and the exact commands. Report the measured values only. If any service sits within 10% of its `mem_limit`, raise that limit and note why.

- [x] **Step 2: Write `.github/workflows/ci.yml`.** Trigger on push and pull_request to `main`. Two jobs:
  - `unit`: `astral-sh/setup-uv`, `uv sync`, `make lint`, `make test`, `make compose-config`
  - `smoke` (needs `unit`): `cp .env.example .env`, `make up`, `make test-int`, then always `make down`


- [x] **Step 3: Verify locally that the workflow is valid YAML and the commands match.**
Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && make check`
Expected: no error.

- [x] **Step 4: Commit and push.** First update `docs/ROADMAP.md`: set phase 0 to done, record the last green commit, and set the Resume block to "Phase 1: write the plan (brainstorming, then writing-plans)".
```bash
git add -A && git commit -m "ci: lint, unit and compose smoke; record phase 0 memory"
```
Creating the GitHub repository and pushing to it is a user decision (public visibility). Then `git push -u origin main`.
Expected: both CI jobs are green on `main`. That is the phase 0 gate.

- [x] **Step 5: Verify the gate** (`superpowers:verification-before-completion`). Check that all of these hold: the CI run URL is green, `make smoke` prints the three rows, `docs/benchmarks/phase0-memory.md` holds the measured values, and the ROADMAP points at phase 1.
