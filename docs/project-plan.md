# F1 Open Lakehouse: Project Plan

Oct 26, 2026 · @Bandya

## Problem statement

**The business problem.** Imagine an F1 analytics team, a broadcaster's data desk or a fan-stats product that must answer questions such as who is really fastest, how much a pit stop cost, and how a driver's form changed over a season. The data they depend on is spread across public APIs with rate limits, arrives late and out of order during a race weekend, and is corrected after the fact (a penalty changes the classified result days later). Without a platform, every analyst builds a private copy, two dashboards show two different championship tables, a correction silently rewrites history, and nobody can say which numbers were true on a given date. This project builds the platform that fixes that: one governed, replayable, queryable source of truth and a fast serving layer on top, so every number can be reproduced and explained.

**What breaks today, and what the pipeline does about it**

| Business pain | Why it happens | What the pipeline provides |
| --- | --- | --- |
| Numbers differ between reports | Each analyst pulls and cleans data separately | One conformed star schema in gold; everyone queries the same definitions |
| A penalty or correction changes a result and nobody knows | Sources overwrite records in place | Iceberg snapshots and versioned facts: query results as of any date and show what changed |
| Live session data is incomplete or out of order | High-frequency events arrive late and duplicated | Replayable streaming ingest with watermarks and idempotent writes |
| Trends break when a team is renamed or a driver moves | Dimensions are overwritten | SCD2 dimensions and inferred members so history stays attributable |
| Dashboards are slow and queries hammer the source APIs | Raw data is queried directly | Columnar serving copy in ClickHouse behind an API, refreshed by partition swap |
| Data quietly goes stale or wrong | No checks or ownership | Airflow freshness and quality gates, lineage, and alerts before bad data is published |
| Nobody trusts or can rebuild the data | No audit trail | Lake is the master copy; every serving table can be rebuilt and audited from it |

The project is also my portfolio evidence for senior data engineering roles; that secondary goal is covered under the learning gap below.

**The secondary goal: the portfolio gap this also closes**

- Current experience covers Spark ETL, Delta Lake on Azure, dimensional modeling, dbt, Airflow, Dagster, Redshift and Synapse.
- Not yet shown: Apache Iceberg, Kafka-API streaming, Spark Structured Streaming, self-hosted object storage, compaction and snapshot expiry, partition evolution, data lineage, and CI for a data project.
- The earlier Airflow project was a basic scheduled DAG. This one uses Airflow's data-aware scheduling, dynamic task mapping, sensors and backfills.

**Why Formula 1 data**

- It is public, event-shaped and versioned by nature: a penalty changes a result after the race ends.
- It has high-frequency timing data, so small-file, late-event and history-tracking problems are real rather than staged.
- Teams are renamed and drivers change teams, which gives slowly changing dimensions a genuine use.

**How it differs from a prediction project**

This is a platform project, not a forecasting one. It asks what happened, how we know it, and what changed afterwards. The core build uses no machine learning, and the design leaves a clean path to add it.

## What it solves

The business pains above reduce to eleven engineering problems, each with a measurable or demonstrable outcome. Rows 1, 2, 3 and 9 give trusted, reproducible numbers; rows 4, 5, 6 and 7 keep live data correct and fast; rows 8, 10 and 11 make the platform explainable and portable.

| # | Problem | How the project answers it | Proof |
| --- | --- | --- | --- |
| 1 | Raw files are not tables | Iceberg tables with schema, ACID commits and snapshots | Snapshot history query |
| 2 | Results are revised after publication | Versioned result facts plus time travel | Provisional vs final result demo |
| 3 | Entities change over time | SCD Type 2 for driver-team and renamed constructors | Career-history query |
| 4 | Streamed events arrive late or twice | Watermarks, idempotent writes, de-duplication | Late-data demo |
| 5 | Streaming creates many small files | Scheduled compaction | File count and scan time before and after |
| 6 | Source schemas change | Schema registry compatibility plus Iceberg schema evolution | One allowed and one rejected change |
| 7 | Queries slow down as data grows | Partitioning, pruning, partition evolution | Bytes scanned before and after |
| 8 | Nobody knows where data came from | OpenLineage events into Marquez | Lineage graph |
| 9 | Bad data reaches dashboards | dbt tests, Airflow checks, schema contracts | Test report with a caught failure |
| 10 | Single-engine lock-in | Spark writes, DuckDB reads the same table | Same query on both engines |
| 11 | It only works on one machine | Docker Compose plus GitHub Actions smoke test | Green CI run, one-command start |

**Goals**

- Everything runs free, on one laptop, with one command.
- Every number on the resume comes from a repeatable benchmark in the repo.
- Every tool choice has a written decision record with the alternatives considered.

**Also in scope:** a dimensional model that follows Kimball standards, a serving layer with a REST API and a web UI that demonstrates the project, a dashboard built on F1 metrics, and design hooks for adding ML later.

**Non-goals**

- No ML models in the core build. The design stays open for them (see ML-ready design).
- No paid services or cloud accounts in the core build.
- No true real-time feed: a recorded session is replayed as a stream.
- No commercial use. This is an unofficial fan project and says so in the README.

## End results

At the end you have a running platform, a set of reproducible proofs, and the documents an interviewer reads. All three groups are required for the project to count as done.

**1. Working system**

| Deliverable | What it is |
| --- | --- |
| One-command environment | Docker Compose (with profiles) starting storage, catalog, streaming bus, Spark, Airflow, ClickHouse, Postgres (metadata only) and the web UI |
| Iceberg lakehouse | Bronze, silver and gold tables on MinIO, managed through a REST catalog |
| Batch backfill | Several seasons of history loaded by an Airflow backfill |
| Streaming path | A recorded session replayed into Redpanda and written to Iceberg by Spark Structured Streaming |
| Transform layer | Spark SQL jobs (run from Airflow) that build silver and gold, with dbt tests, contracts and docs on top |
| Maintenance jobs | Scheduled compaction, snapshot expiry and orphan-file cleanup |
| Serving layer | Gold marts copied to ClickHouse, exposed through a REST API and shown in a web UI |
| CI | GitHub Actions running lint, unit tests, DAG import tests and a compose smoke test |

**2. Proof (the part that backs resume claims)**

- A benchmark report with before and after numbers for compaction and partition pruning.
- A time-travel demo showing a result as first published and as corrected after a penalty.
- A schema-evolution demo: one compatible change accepted, one incompatible change rejected.
- A late-data demo showing events handled by the watermark.
- A multi-engine demo: the same Iceberg table queried from Spark and DuckDB.
- A test report that shows at least one real data problem being caught.

**3. Documents**

- README with an architecture diagram and a quick start.
- A case study: problem, decisions, what broke, what you would change.
- Architecture decision records, one per major tool choice.
- A "what changes at 100x scale" page.

**Definition of done**

- [ ] A fresh clone starts with one command and the dashboard shows data.
- [ ] CI is green on the main branch.
- [ ] Each benchmark can be re-run from a documented command.
- [ ] Every resume number traces to a benchmark in the repo.
- [ ] The README states the data sources, licenses and the unofficial fan-project disclaimer.

## Data and questions

The data is public and free, and it answers five analytical questions about pit strategy, tyres and race control. Source details below come from the race-calls README and from memory, so check each provider's current endpoints, rate limits and terms before building.

| Source | Gives | Used for |
| --- | --- | --- |
| [Jolpica](https://github.com/jolpica/jolpica-f1) (Ergast-compatible) | Calendar, qualifying, results, standings, historical seasons | Batch backfill and the official record |
| [OpenF1](https://openf1.org) | Weather, race control messages, laps, positions; from memory also pit stops, stints and car data | Session data and the streaming replay |
| [f1db](https://github.com/f1db/f1db) (pinned release) | Grid-slot history, engine suppliers | Reference tables |

OpenF1 history is available about 30 minutes after a session ends, according to the race-calls README. Real-time access is believed to be paid, so the streaming path replays recorded sessions at an adjustable speed.

**The five questions the gold layer answers**

1. Which teams have the fastest pit stops, by season?
2. Did pitting early (an undercut) gain places?
3. How quickly do tyres degrade, by compound and stint?
4. How do safety cars reshuffle the running order?
5. How consistent is each driver across sector times?

**Data handling rules**

- Cache every raw API response in the landing zone so each endpoint is called once.
- Keep telemetry to a few sessions at first. It is the largest table and the main source of small files.
- Add a disclaimer that this is an unofficial, non-commercial fan project, and respect each source's license.

## Architecture

&#91;embedded content: local open lakehouse architecture · two lanes into one Iceberg store\]

Two lanes feed the same bronze tables: a batch lane from Jolpica and f1db, and a streaming lane that replays OpenF1 sessions through Redpanda. Silver and gold are built with dbt, DuckDB reads any layer, and only the gold marts reach ClickHouse and, through the API, the web UI. Airflow schedules every step.

## Tech stack

The core stack is entirely open source and free. Airflow replaces Dagster as the orchestrator, because Airflow is named more often in job postings and this build uses its advanced features. Tool behaviour below is described from memory, so verify versions and licenses before committing.

| Layer | Chosen | Alternatives | Why chosen |
| --- | --- | --- | --- |
| Streaming bus | Redpanda | Apache Kafka (KRaft), Redis Streams, Pulsar, NATS | Kafka-compatible API, single binary, built-in schema registry, light on memory |
| Object storage | MinIO | SeaweedFS, Garage, LocalStack S3 | Standard local S3. Check its current license and packaging; keep SeaweedFS or Garage as fallback |
| Table format | Apache Iceberg | Delta Lake OSS, Apache Hudi, Apache Paimon | New skill beyond existing Delta experience; engine-neutral |
| Catalog | Apache Polaris | Project Nessie, Lakekeeper, Hive Metastore, JDBC catalog | Vendor-neutral REST catalog. Phase 0 starts with a JDBC catalog; swap to Polaris or Lakekeeper once the write path works |
| Batch and streaming compute | Apache Spark | Apache Flink, Polars, Daft | Already known; Structured Streaming and Iceberg maintenance procedures |
| Fast analytics | DuckDB | Trino, DataFusion | Single binary, reads Iceberg and Parquet, shows multi-engine reads |
| Transformation | dbt | SQLMesh | Industry standard. Used for tests, contracts and docs; Spark SQL does the Iceberg writes because dbt writing to Iceberg is unproven (prove it in phase 0) |
| Orchestration | Apache Airflow | Dagster, Prefect, Kestra | Most requested; advanced features planned below |
| Lineage | OpenLineage + Marquez | DataHub, OpenMetadata, dbt docs only | Airflow and Spark can emit OpenLineage events |
| Data quality | dbt tests, Airflow checks, Pydantic | Great Expectations, Soda Core, Pandera | Light, already familiar |
| Serving database | ClickHouse | PostgreSQL (fallback), StarRocks | Columnar OLAP copy of gold for fast dashboards; the lake stays the source of truth. Postgres remains only for Airflow and catalog metadata |
| API and UI | FastAPI and a React web UI | Streamlit, Evidence, Superset, Grafana | Shows the platform end to end; fall back to Streamlit if time is short |
| Containers | Docker Compose on WSL2 | Podman Compose, kind | Reproducible start for reviewers |
| CI | GitHub Actions | GitLab CI | Free for public repos |
| Packaging | uv | Poetry, pip-tools | Fast, reproducible Python environments |

**Two risk-reducing substitutions**

- Start with a JDBC catalog to unblock the write path, then move to Polaris or Lakekeeper.
- Treat Marquez, Superset and Trino as stretch goals. The core is phases 0 to 4.

## Data model

Tables follow a medallion layout. Names and columns are a proposed starting point and will be refined in phase 1. Gold holds the star schema described in the dimensional model section, and the question marts below are built on top of it.

| Layer | Table | Grain and key | Partitioning | Notes |
| --- | --- | --- | --- | --- |
| Landing | raw JSON files | one file per API request | by source and fetch date | Immutable; enables full rebuild |
| Bronze | results, qualifying, sessions | driver per session | season, round | Append-only, with ingested\_at |
| Bronze | laps, pit\_stops, stints | driver per lap or stop | season, round | Append-only |
| Bronze | race\_control, weather | event timestamp | season, round | Streamed path writes here too |
| Bronze | car\_data (optional) | sample timestamp | session | Largest table; drives compaction |
| Silver | dim\_driver\_team | driver, constructor, valid\_from | none | SCD Type 2 with is\_current |
| Silver | results\_versions | result per driver per version | season, round | Keeps provisional and final results |
| Silver | laps\_clean, stints\_clean | driver per lap | season, round | De-duplicated, typed, late events resolved |
| Silver | pit\_stops\_clean | driver per stop | season, round | Linked to stint and lap |
| Gold | pit\_stop\_leaderboard | team per season | season | Question 1 |
| Gold | undercut\_analysis | driver per race | season | Question 2 |
| Gold | tyre\_degradation | stint per compound | season | Question 3 |
| Gold | safety\_car\_impact | race | season | Question 4 |
| Gold | sector\_consistency | driver per season | season | Question 5 |

**Design rules**

- Bronze is append-only and carries an ingested\_at column, so every row can be traced to when it was learned.
- Re-running any load must not create duplicates. Each load writes by a natural key or overwrites a whole partition.
- Result changes are never updated in place. A new version row is added and the previous version is closed.

## Dimensional model

Gold follows Kimball dimensional modeling: every fact table has a declared grain, facts share conformed dimensions through surrogate keys, and the layout supports the standard OLAP operations (slice, dice, roll-up, drill-down). The layers above say where data lives; this section says how it is shaped. Which source feeds each table (Jolpica, OpenF1, f1db) is from memory and must be confirmed when the incoming data is profiled.

**Standards applied**

- Four steps in order: pick the business process, declare the grain, choose the dimensions, then the facts. The grain is written down before any column.
- Conformed dimensions: one dim\_driver, one dim\_constructor, one dim\_circuit shared by every fact, so results from different facts can be combined (drill-across).
- Surrogate keys on every dimension, built as deterministic hashes so loads are idempotent. Natural keys (Jolpica driverId, OpenF1 driver\_number) stay as attributes.
- Slowly changing dimensions chosen per attribute: Type 1 for corrections, Type 2 where history matters (constructor name and engine supplier, circuit layout, driver and team assignments).
- Facts store the surrogate key that was valid at event time, so historical queries need no date-range joins.
- Every fact type is used where it fits: transaction, periodic snapshot, accumulating snapshot and factless.
- Measures are classified as additive, semi-additive or non-additive. Ratios are stored as numerator and denominator and computed in the metric layer, never averaged.
- Degenerate dimensions (lap number, result version), a junk dimension for track condition flags, and role-playing dates (race date and ingestion date from one dim\_date).
- Unknown and inferred members: a row with key -1 for missing references, and an inferred dimension row created when a fact arrives before its dimension (late-arriving dimension), corrected later.
- Times are stored as integer milliseconds and UTC timestamps, never as formatted strings.
- Naming: dim\_, fact\_, agg\_ and mart\_ prefixes, snake\_case, \_key for surrogate and \_id for natural keys. Audit columns on every table: ingested\_at, source, batch\_id, row\_hash, and valid\_from, valid\_to, is\_current where history is kept.

**Dimensions**

| Dimension | Grain | Main attributes | Change policy |
| --- | --- | --- | --- |
| dim\_date | One calendar day | Date, year, month, week, weekday, is\_race\_day | Static |
| dim\_race\_weekend | One grand prix weekend | Season, round, grand prix name, sprint flag, circuit key | Type 1 |
| dim\_session | One session | Session type (practice, sprint qualifying, sprint, qualifying, race), scheduled start | Type 1 |
| dim\_circuit | One circuit layout version | Circuit id, name, country, layout version, length | Type 2 |
| dim\_driver | One driver | Driver id, name, code, nationality, birth date, permanent number | Type 1; Type 2 for number or code changes |
| dim\_constructor | One constructor identity | Name, nationality, engine supplier | Type 2 (renames, power-unit changes) |
| bridge\_driver\_constructor | Driver, constructor and effective dates | Valid from, valid to | Type 2. Used at load time to stamp constructor\_key onto facts, and for career history |
| dim\_tyre\_compound | One compound | Soft, medium, hard, intermediate, wet; colour | Static |
| dim\_finish\_status | One finish status | Status text, category (finished, lapped, mechanical, accident, disqualified, other) | Type 1 |
| dim\_track\_condition | One combination of flags (junk dimension) | Dry, damp or wet; green, safety car, virtual safety car or red flag | Static, built from combinations |
| dim\_event\_type | Race control category and flag | Category, flag, scope | Static |

**Facts**

| Fact | Type | Grain | Main measures |
| --- | --- | --- | --- |
| fact\_race\_result | Transaction, versioned | One driver, one race or sprint, one result version | Grid position, finish position, points, laps completed, race time ms, fastest-lap flag. Degenerate: result version and is\_current |
| fact\_qualifying\_result | Transaction | One driver per qualifying session | Q1, Q2, Q3 times ms, final position |
| fact\_lap | Transaction | One driver per lap per session | Lap time ms, sector times ms, speed-trap speeds, tyre age, pit-in and pit-out flags |
| fact\_stint | Transaction | One driver per stint | Laps in stint, starting tyre age, average lap time, degradation slope (derived) |
| fact\_pit\_stop | Transaction | One driver per stop | Pit-lane duration ms, lap number, stop number |
| fact\_position | Periodic snapshot | One driver per lap end | Running position, gap to leader, interval to car ahead |
| fact\_race\_control\_event | Transaction (event) | One race control message | Event count (1) |
| fact\_weather | Periodic snapshot | One session per time interval | Air and track temperature, humidity, wind speed, rain flag |
| fact\_telemetry\_sample (optional) | Transaction | One driver per sample | Speed, rpm, gear, throttle, brake, DRS state |
| fact\_driver\_standings | Periodic snapshot | One driver per season per round | Cumulative points, wins, position |
| fact\_constructor\_standings | Periodic snapshot | One constructor per season per round | Cumulative points, position |
| fact\_weekend\_data\_status | Accumulating snapshot | One race weekend | Timestamps for when sessions landed, results turned provisional, results turned final, gold was published, and the lags between them |
| fact\_driver\_entry | Factless | One driver per race weekend | None. Counts entries, did-not-start and did-not-qualify |

Versioned results work like this: a penalty adds a new version row and closes the previous one, so provisional and final results both stay queryable. A current view (is\_current = true) is what most dashboards read.

**Bus matrix** (x marks a conformed dimension that the fact uses)

| Fact | Date | Weekend | Session | Driver | Constructor | Circuit | Tyre | Status | Condition | Event |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fact\_race\_result | x | x | x | x | x | x |  | x |  |  |
| fact\_qualifying\_result | x | x | x | x | x | x |  |  |  |  |
| fact\_lap | x | x | x | x | x | x | x |  | x |  |
| fact\_stint | x | x | x | x | x | x | x |  |  |  |
| fact\_pit\_stop | x | x | x | x | x | x |  |  |  |  |
| fact\_position | x | x | x | x | x | x |  |  | x |  |
| fact\_race\_control\_event | x | x | x |  |  | x |  |  | x | x |
| fact\_weather | x | x | x |  |  | x |  |  | x |  |
| fact\_telemetry\_sample | x | x | x | x | x | x |  |  |  |  |
| fact\_driver\_standings | x | x |  | x | x |  |  |  |  |  |
| fact\_constructor\_standings | x | x |  |  | x |  |  |  |  |  |
| fact\_driver\_entry | x | x |  | x | x | x |  | x |  |  |
| fact\_weekend\_data\_status | x | x |  |  |  | x |  |  |  |  |

**OLAP behaviour**

- Slice and dice: filters on season, circuit, constructor, compound and session type. These are plain dimension filters in the API and UI.
- Roll-up and drill-down along the hierarchies lap, stint, race, season and driver, constructor, team history. Totals at each level come from GROUPING SETS or ROLLUP in DuckDB and ClickHouse.
- Aggregate tables for the heavy views: agg\_driver\_season, agg\_constructor\_season, agg\_circuit\_history and agg\_stint\_compound. They are rebuilt incrementally and served from ClickHouse as pre-aggregated tables or materialized views.
- Metric definitions live in one place (documented dbt models), so the UI and API never recompute a metric differently. A semantic-layer tool is optional; check licensing before adopting one.

## Metrics and dashboard

The dashboard uses measures that analysts, broadcasters and teams commonly use to judge F1 performance, each defined once with a formula, a grain and a source fact. The list is a starting point. After the incoming data has been profiled, drop metrics the data cannot support and add ones it reveals. Whether a field exists (for example stationary pit time, or fuel-corrected lap times) must be confirmed against the real feeds.

**Metric catalogue**

| Metric | Definition | Source facts | Page |
| --- | --- | --- | --- |
| Championship progression | Cumulative points per driver and constructor after each round | fact\_driver\_standings, fact\_constructor\_standings | Season |
| Wins, podiums, poles | Counts and rates per driver and constructor | fact\_race\_result, fact\_qualifying\_result | Season |
| Pole-to-win conversion | Wins from pole divided by poles | fact\_race\_result | Season |
| Points per start | Points divided by races started | fact\_race\_result | Season |
| Reliability (DNF rate) | Retirements with a mechanical status divided by starts, by constructor | fact\_race\_result, dim\_finish\_status | Team |
| Qualifying gap to pole | (driver best time minus pole time) divided by pole time, as a percentage | fact\_qualifying\_result | Driver, Weekend |
| Teammate head-to-head | Qualifying and race wins against the teammate, and the average gap, which removes most of the car effect | fact\_qualifying\_result, fact\_race\_result | Driver |
| Positions gained | Grid position minus finish position | fact\_race\_result | Weekend, Driver |
| Lap-1 positions gained | Position after lap 1 versus grid position | fact\_position | Weekend |
| Race pace | Median lap time on green-flag, clean-air laps, excluding in and out laps and neutralised laps, shown as a percentage off the best median in the race | fact\_lap | Weekend, Team |
| Lap-time consistency | Standard deviation of green-flag lap times within a stint | fact\_lap | Driver |
| Sector bests | Count of best sector times per driver and team | fact\_lap | Weekend |
| Top speed | Highest speed-trap reading per driver and race | fact\_lap | Weekend, Team |
| Pit stop time | Median pit-lane duration per team with the sample size shown (stationary time if the feed has it) | fact\_pit\_stop | Strategy |
| Stint length and stop count | Laps per stint, number of stops, one-stop versus two-stop mix | fact\_stint | Strategy |
| Tyre degradation | Slope of lap time against tyre age within a stint, per compound and circuit. Fuel burn hides degradation, so show a fuel-corrected variant if the data allows | fact\_lap, fact\_stint | Strategy |
| Undercut success | A driver pits before a rival within a set number of laps, and is ahead after the rival stops. The threshold is a parameter | fact\_pit\_stop, fact\_position | Strategy |
| On-track versus pit position change | Net positions gained excluding changes caused by pit cycles | fact\_position, fact\_pit\_stop | Weekend |
| Neutralisation impact | Number of safety car and virtual safety car periods, laps under them, and the sum of absolute position changes across restarts | fact\_race\_control\_event, fact\_position | Weekend |
| Weather effect | Difference in results and pace between wet and dry sessions | fact\_weather, fact\_lap | Season |
| Data freshness and quality | Lag from session end to gold published, test pass rate, row counts, file counts, compaction savings | fact\_weekend\_data\_status, Iceberg metadata | Platform |

**Dashboard pages**

| Page | Main views | OLAP interaction |
| --- | --- | --- |
| Season overview | Championship progression lines, wins and podiums table, reliability heat map by constructor and race | Filter by season; roll up from drivers to constructors |
| Race weekend report | Grid versus finish, lap chart of running positions, race pace by driver, pit stop timeline, safety car markers, weather strip | Drill down from session to lap |
| Driver profile | Teammate head-to-head, consistency, qualifying gap trend, career timeline across teams from the SCD2 history | Slice by season and circuit |
| Team and strategy | Pit time distribution, tyre strategy strips per driver coloured by compound, degradation by compound, undercut table | Dice by circuit and compound |
| Platform and data quality | Lineage graph, freshness and test results, a time-travel viewer showing a result as first published and as corrected, compaction before and after, benchmark numbers | Choose a table snapshot |

The platform page is what separates this from a plain F1 stats site: it shows the engineering evidence next to the analytics.

## Airflow design

Airflow is the orchestrator and the part of the project that fixes the earlier basic DAG. Feature names follow Airflow 3 conventions (datasets are now called assets); confirm against the current docs.

| DAG | Trigger | Advanced feature shown |
| --- | --- | --- |
| f1\_batch\_backfill | Manual, with backfill by season | Dynamic task mapping (one task per season), data intervals, idempotent writes |
| f1\_session\_ingest | Schedule on race weekends | Sensor or deferrable operator waiting until OpenF1 data is available |
| f1\_stream\_replay | Manual or scheduled | Replay producer into Redpanda; monitoring task on the Spark stream |
| f1\_silver\_build | When bronze assets update | Data-aware (asset) scheduling; dbt models as individual tasks |
| f1\_gold\_publish | After silver | Star schema and marts built, then published to ClickHouse |
| f1\_table\_maintenance | Daily | Compaction, snapshot expiry, orphan-file removal, with before and after metrics logged |
| f1\_quality\_freshness | After each load | Row-count, freshness and schema checks; failure alerts |

**Practices applied across all DAGs**

- TaskFlow API for readable Python tasks.
- A shared pool to respect API rate limits.
- Retries with backoff and failure callbacks.
- A custom hook for the Jolpica and OpenF1 clients, with response caching.
- OpenLineage provider enabled so lineage reaches Marquez.
- DAG import tests and a dry run in CI.

**Resource note:** Airflow with LocalExecutor uses roughly 3 to 4 GB of RAM across its containers (approximate). Do not use the Celery executor on a laptop.

## Serving layer and UI

Serving is its own layer: gold tables are published to ClickHouse, a typed REST API exposes them, and a web UI shows the dashboards and a platform page that demonstrates the engineering. Nothing in the UI reads the lake directly except the time-travel audit view.

&#91;embedded content: serving layer · gold to ClickHouse to API to UI, plus static demo\]

The left-to-right path publishes gold into ClickHouse, which feeds the API and then the UI. The highlighted DuckDB path is the exception: it reads Iceberg snapshots so the UI can show a result as it was first published. The bottom row builds a static copy of the UI that reviewers can open without running Docker.

**API surface** (paths are illustrative and will follow the final marts)

| Endpoint | Returns | Reads from |
| --- | --- | --- |
| GET /v1/seasons/{year}/standings | Championship tables and progression | ClickHouse |
| GET /v1/races/{season}/{round}/results?version=final | Provisional or final classification | ClickHouse |
| GET /v1/races/{season}/{round}/laps?driver=... | Lap table with pace metrics | ClickHouse |
| GET /v1/strategy/tyre-degradation?circuit=...&compound=... | Degradation slopes | ClickHouse |
| GET /v1/audit/results?asof=... | A result as of a timestamp or snapshot id | Iceberg through DuckDB |
| GET /v1/platform/health | Freshness, test results, file counts | ClickHouse and Iceberg metadata |
| GET /v1/platform/lineage | Lineage graph | Marquez, or dbt docs as fallback |

**API practices:** OpenAPI documentation generated from the code, Pydantic response models, versioned paths, pagination and dimension filters as parameters, cache headers, a read-only database role, a health endpoint, and contract tests in CI.

**Web UI**

| Option | Notes |
| --- | --- |
| React, Vite, TypeScript and Apache ECharts (recommended) | Full control for lap charts, tyre strategy strips and a time-travel slider. Most work, strongest result |
| Observable Plot or Plotly for charts | Lighter than ECharts, less custom |
| Streamlit or Evidence (fallback) | Python or SQL only and much faster to build, but looks less like a product |
| Superset on ClickHouse (optional) | Analyst self-serve exploration over the same marts. Keep only if time allows |

Build the UI on the five pages from the dashboard section. Budget about 2 weeks for the API and UI together (estimate).

**Two ways to run it**

- Live mode: the full Compose stack, with the UI reading the API. Used for development and for live walkthroughs.
- Static demo mode: an Airflow DAG exports a snapshot of the gold marts and platform metrics as JSON or Parquet, the UI is built against that snapshot, and the result is hosted on free static hosting such as GitHub Pages or Cloudflare Pages (check current terms and size limits). The time-travel view uses pre-exported snapshots in this mode.

**Airflow DAGs added for serving**

- f1\_dimension\_load: loads dimensions before facts, with inferred members for late-arriving references.
- f1\_gold\_publish: publishes the star schema and marts into ClickHouse, replacing only the changed fact partitions and reloading the small dimensions.
- f1\_serving\_checks: row-count and checksum parity between Iceberg gold and ClickHouse.
- f1\_demo\_export: writes the static snapshot and rebuilds the demo site.

## Serving store and refresh strategy

ClickHouse is the single serving database: a columnar copy of the gold tables that the API queries. Iceberg stays the source of truth, all corrections and history are handled in the lake, and ClickHouse only receives finished tables by partition. ClickHouse details here are from memory and must be checked against its current documentation.

**Where each layer lives.** No database holds the intermediate layers. They are files in object storage with table metadata on top.

| Layer | Where | Format | Written by | Read by |
| --- | --- | --- | --- | --- |
| Landing | MinIO bucket, one file per API request | JSON as received | Airflow tasks | Spark |
| Bronze | MinIO, Iceberg tables | Parquet | Spark | Spark, DuckDB |
| Silver | MinIO, Iceberg tables | Parquet | Spark SQL | Spark, DuckDB |
| Gold (star schema) | MinIO, Iceberg tables | Parquet | Spark SQL | Spark, DuckDB, publish job |
| Serving copy | ClickHouse | Native columnar tables | Publish job | API |

```
MinIO
  landing/      raw JSON files
  warehouse/
    bronze/     Iceberg tables
    silver/     Iceberg tables
    gold/       Iceberg tables  -->  copy  -->  ClickHouse
```

**Roles of the databases and engines**

| Component | A warehouse? | Role |
| --- | --- | --- |
| Iceberg on MinIO | Yes, the lakehouse | Holds all data, history and time travel |
| DuckDB | No | Query engine with no server and no data of its own; used for transforms and the audit page |
| ClickHouse | Serving store | Columnar copy of gold for dashboards |
| PostgreSQL | No | Bookkeeping for Airflow, the Iceberg catalog and Marquez. It never holds F1 data |

**How updates are handled.** Corrections, late-arriving dimensions and SCD2 history are changes in the lake, where Iceberg handles them well. ClickHouse never updates single rows; it receives replacement partitions.

| Case | In the lake (Iceberg) | In ClickHouse |
| --- | --- | --- |
| Result corrected by a penalty | MERGE into the versioned fact: a new version row, the old one closed | Replace that race's partition (season, round) |
| Late-arriving dimension | An inferred member is created with a deterministic key; real attributes overwrite it later (Type 1) | Reload the dimension in full, since it is small. Facts are unchanged because the key never changed |
| Backdated SCD2 change | Re-stamp keys on the affected fact rows and rewrite only those partitions | Replace those partitions |
| Standings after each round | Append a new snapshot | Insert only |
| Streamed laps and positions | Late events inside the watermark are fixed in Spark; later ones trigger a partition reprocess | Insert, or replace the partition after a reprocess |
| Time travel | Iceberg snapshots | Not stored. The audit page reads Iceberg through DuckDB |

**ClickHouse loading rules (verify in the docs)**

- Load into a staging table, then swap the partition or table in, so readers see the old or the new copy and never a mix.
- Reload small dimension tables in full with a table swap.
- Avoid row-level UPDATE and DELETE. If a versioned-row engine such as ReplacingMergeTree is used, duplicates only disappear after background merges, so queries need care.
- Choose sort keys from the dashboard filters (season, round, driver) and partition by season.
- Make every publish idempotent with a batch id, then run the parity check: row counts and checksums, lake versus ClickHouse.

**Fallback and triggers.** The API reaches the serving store through one module, so it can be swapped. Switch to Postgres as the serving store if ClickHouse memory does not fit the laptop budget, partition swaps prove too fiddly, or the benchmark shows no measurable benefit.

**Optional benchmark:** run the same five dashboard queries on ClickHouse, Postgres and DuckDB reading Iceberg directly, and record median times. Report only measured numbers.

## The debate behind the storage and serving choices

This section records the questions raised while choosing the serving store, the positions taken, and how each was resolved, so the reasoning can be reread later and reused in interviews.

| # | Question | Positions | Resolution |
| --- | --- | --- | --- |
| 1 | Is ClickHouse a storage format like Parquet or Iceberg? | It looked like one, because the lake is already columnar | No. Parquet is files, Iceberg is a list of files plus table metadata, and ClickHouse is a running database server with its own storage engine. Columnar describes how data is laid out, not which layer it belongs to |
| 2 | If the lake is already columnar, why add ClickHouse? | For: fast concurrent dashboard queries through sort keys and indexes. Against: duplicate data, freshness lag, one more service | Add it as a serving copy only. The lake remains the master and the copy can be rebuilt at any time |
| 3 | Row or columnar for the serving store? | Row (Postgres) versus columnar (ClickHouse) | Columnar. Analytics read a few columns across many rows, and the project has no row-by-row transaction workload. The cost is slow single-row updates, handled in question 5 |
| 4 | Are Postgres, ClickHouse and DuckDB three warehouses? | A worry that the design contained three | No. There is one serving database. DuckDB is a query engine with no server or data of its own, and Postgres only holds bookkeeping for other tools |
| 5 | Late-arriving dimensions, SCD2 and time travel imply frequent updates, and ClickHouse is weak at updates | Wrong tool for updatable data | Updates happen in Iceberg, and ClickHouse receives replacement partitions. The changes are occasional corrections, not row-by-row traffic. Time travel stays in Iceberg |
| 6 | Where do raw, staged and gold data live? | Which database holds them | In MinIO as files, with Iceberg tables over Parquet. A small catalog database holds table pointers, never the data |
| 7 | ClickHouse or Postgres at this data size? | Postgres is enough for F1 volumes. ClickHouse fits an OLAP project and appears in a posting | ClickHouse as the primary serving store, Postgres as the fallback, with the swap isolated in one API module |

**Why ClickHouse is in the plan at all.** An HPE Cloud Developer and Data Engineer posting (2 to 4 years of experience) names Kafka, Spark, ClickHouse, Docker, CI/CD and distributed systems. Using it keeps the project aligned with roles the target market actually posts.

**Earlier decision: local open stack or Databricks first.** Five senior data engineer postings on Indeed were read on 2026-10-26. The sample is tiny and keyword-biased, so treat it as directional.

| Posting | Databricks | Kafka | Iceberg or open table formats |
| --- | --- | --- | --- |
| [Software Mechanics, Bengaluru](https://to.indeed.com/aazsssptmlrb) | no | yes | yes |
| [HPE, Bengaluru](https://to.indeed.com/aa29bnkw8fq8) | no | yes (exposure) | yes |
| [LSEG, Bengaluru](https://to.indeed.com/aapfwgc6hth8) | no | no | yes |
| [Mastercard, Hyderabad](https://to.indeed.com/aa4wlvcyfm6g) | yes | no | no |
| [Madhjyoti, Pune](https://to.indeed.com/aapj499rg7fq) | yes | yes | no |

Iceberg and Kafka each appeared in three of five requirement lists, and Databricks in two. Databricks is a smaller step from existing Spark, PySpark, Delta Lake and Azure experience than Kafka and Iceberg are, and only the local stack can teach those two.

**Final decisions**

| Choice | Decision | Revisit if |
| --- | --- | --- |
| Serving store | ClickHouse | Memory does not fit, partition swaps prove too fiddly, or the benchmark shows no benefit |
| Serving fallback | Postgres, behind the same API module | ClickHouse is dropped |
| Intermediate layers | Iceberg on MinIO, Parquet files | Phase 0 shows the write path does not work |
| DuckDB | Query engine for transforms and the audit page | Spark covers both without it |
| Platform track | Local open stack (phases 0 to 4). The Databricks leg is optional, after phase 3 | Laptop RAM is 8 GB or less, which makes Databricks-first the choice |

**Still to verify:** ClickHouse licensing and memory use, how partition swaps behave in the version you install, and whether dbt can write to Iceberg through DuckDB.

## ML-ready design

The core build contains no models, but six design decisions keep predictions possible later without reworking the platform. Each one is ordinary data engineering that is useful on its own, so none of it needs machine learning knowledge now.

| Hook | What it is | Why it matters later | Cost now |
| --- | --- | --- | --- |
| Point-in-time correctness | Every fact has an event time and an ingested\_at. Iceberg snapshots allow as-of queries. A dbt test fails if a feature is newer than the time a prediction was made | Prevents leakage, the most common ML data bug | Already in the plan |
| Feature tables | Tables such as feature\_driver\_race with one row per driver per race, holding only values known before the race (grid, recent form, circuit history). Built from the star schema | One definition reused by any model | One dbt model per table |
| Label tables | label\_race\_outcome, built only after results are final, keyed the same way as the features | Clean date-based train and test splits | One dbt model |
| Reserved prediction schema | dim\_model (name, version, trained\_at, feature set) and fact\_prediction (model key, entity keys, made\_at, predicted value or probability, run type backtest or live), plus a score fact | Model output becomes one more conformed fact, so dashboards and the API serve it unchanged | Empty tables only |
| Experiment tracking | MLflow (open source) when models arrive. A feature store such as Feast is probably too heavy at this scale | Traceability of which model made which prediction | None now |
| API and UI slot | A /v1/predictions endpoint and a UI page stub marked not enabled | Shows the extension path to a reviewer | Small |

**When you decide to add ML**

- Start with baselines (historical rate for each grid slot, recent form) before any model, so every model has something simple to beat.
- Judge probabilities with Brier score and a calibration table, not accuracy alone.
- Keep backtests and live predictions separate through the run type column.

**Scope note:** prediction ledgers are the centre of some other F1 projects. Here they stay an extension hook, and the main story remains the platform. This work is optional (phase 7) and not needed for the project to count as finished.

**One-line answer for interviews:** the platform is ML-ready through point-in-time feature tables, separate label tables, a reserved prediction schema and snapshot-based reproducibility.

## Phase plan

The build takes about 8 to 10 weeks part-time, and the serving API and UI is the largest single phase. Each phase ends with a gate that must pass before the next one starts, and phase 0 is deliberately small so the riskiest piece (writing Iceberg tables) is proven first.

&#91;embedded content: phase roadmap · eight phases with exit gates\]

| Phase | Key tasks |
| --- | --- |
| 0 Foundation | Create the repo, Makefile and CI skeleton. Compose with MinIO, a JDBC catalog and Spark. Write and read one Iceberg table. Measure memory with docker stats |
| 1 Batch backfill, dimensions | Airflow f1\_batch\_backfill with one mapped task per season. Bronze tables. Conformed dimensions with SCD2 (constructor, circuit, driver assignments). fact\_race\_result and fact\_qualifying\_result with result versions. Bus matrix and dbt tests. A time-travel query on a corrected result |
| 2 Streaming | Replay producer. Redpanda topics and registry schemas. Structured Streaming writer with a watermark. fact\_lap, fact\_position and fact\_race\_control\_event loaded. Watch the small files appear |
| 3 Maintenance, multi-engine | f1\_table\_maintenance DAG. Partition evolution. DuckDB reads. Benchmark scripts and report. Swap to Polaris or Lakekeeper if stable |
| 4 Serving API and UI | f1\_gold\_publish into ClickHouse (partition replace for facts, full reload for dimensions) with a parity check. FastAPI with typed endpoints. React UI with five pages, including the time-travel audit view. Metric definitions reviewed against the real data |
| 5 Quality and lineage | dbt tests and contracts. Airflow freshness checks. OpenLineage into Marquez, or dbt docs lineage as fallback. A documented caught failure |
| 6 Demo and polish | f1\_demo\_export and a free static host. README, case study, decision records. Fresh-clone test |
| 7 ML-ready hooks (optional) | Feature and label tables with a leakage test. Empty dim\_model and fact\_prediction tables. A predictions API stub and UI page marked not enabled |
| 8 Databricks leg (optional) | Only after phase 3 and only if time allows. Load the same history into Databricks Free Edition, run the egress test first, rebuild one mart on Delta, and write a decision record on open versus managed. About one week (estimate) |

## Quality, lineage and governance

Data quality is checked at three points, so a problem is caught at the earliest layer where it can be seen.

| Stage | Control | Example |
| --- | --- | --- |
| Ingestion | Pydantic models validate each API response; the schema registry enforces compatibility on streamed events | A malformed lap record is rejected and logged, not written |
| Bronze to silver | dbt tests: not null, unique, accepted values, relationships | No duplicate lap per driver; every pit stop has a known driver |
| Silver to gold | dbt model contracts and row-count reconciliation | Gold totals match silver for the same season |
| Orchestration | Airflow checks for freshness and volume after each load | Alert if a race weekend produced zero rows |

**Lineage:** Airflow and Spark emit OpenLineage events to Marquez, so the graph from source to dashboard is visible. If Marquez is too heavy for the laptop, fall back to dbt docs lineage and say so in the README.

**Contracts:** schema changes follow a written policy. Additive changes (a new column) are accepted automatically; renames, drops and type changes need review and a new version. This policy is itself one of the decision records.

## Benchmarks and proof

Every claim on the resume must come from one of these experiments. Record the machine specification, repeat each run several times, and report the median. Do not put a number on the resume until it has been measured.

| Experiment | Method | Metric | Resume claim template |
| --- | --- | --- | --- |
| Compaction | Stream a session, count files, run compaction, re-run a fixed query | File count; query time | Reduced file count by \[X\]% and scan time by \[Y\]% |
| Partition pruning | Same query with and without a season and round filter; inspect the plan | Bytes or files scanned | Cut data scanned by \[X\]% through partitioning |
| Partition evolution | Change the partition spec after data exists, without rewriting old files | Rewrite avoided; query still correct | Evolved partitioning without a table rewrite |
| Time travel | Query a result at the first snapshot and after a penalty correction | Two differing answers, both reproducible | Reproduced prior results via snapshot queries |
| Schema evolution | Add a compatible field, then attempt an incompatible one | One accepted, one rejected | Enforced schema compatibility on streamed events |
| Late data | Replay events out of order past the watermark | Events kept or dropped as designed | Handled late-arriving events with watermarking |
| Multi-engine | Run one query from Spark and DuckDB | Same result; timings | Served one Iceberg table to two engines |
| Idempotency | Re-run a load twice | Identical row counts | Idempotent loads verified by re-run |
| Reproducibility | Fresh clone in CI | Green smoke test | One-command environment validated in CI |

## Alternative track: fully cloud on Databricks

A cloud-only version is feasible and needs almost no laptop RAM, but it replaces the open stack rather than extending it: the same F1 data and questions, built on Delta Lake and Unity Catalog. It adds Databricks keywords that the current resume lacks, and it loses Iceberg, Kafka-API streaming and self-hosted storage.

**Why it replaces the local stack instead of plugging into it**

- Free Edition runs on serverless compute only, and custom workspace storage locations are not supported, so MinIO cannot back it.
- Outbound internet access is limited to a set of trusted domains. A local Redpanda is not reachable from the cloud, and whether the F1 API hosts are allowed is unknown until tested. I could not find a published list of allowed domains.
- Delta Lake and Unity Catalog are native, which suits a Databricks-first build but overlaps with existing Delta experience.

&#91;embedded content: cloud-only architecture · Databricks Free Edition\]

The Job fetches data into a Volume, Auto Loader streams the arriving files into Delta tables, and a SQL warehouse serves dashboards. If the APIs are blocked, a scheduled GitHub Actions job uploads the files instead.

**How each local component maps**

| Local stack | Databricks track | Note |
| --- | --- | --- |
| MinIO | Unity Catalog Volumes and managed tables | No custom storage locations |
| Iceberg and a catalog | Delta tables in Unity Catalog | The Iceberg keyword exists only in the local track |
| Redpanda and Structured Streaming | Auto Loader over arriving files | File-based micro-batches, not a message broker. Say so in interviews |
| Airflow | Databricks Jobs, optionally triggered by Airflow | Needs workspace API access from outside; test it |
| dbt and DuckDB | dbt or SQL on the warehouse, or Lakeflow pipelines | Verify the dbt adapter works on Free Edition |
| Compaction and snapshot expiry | OPTIMIZE and VACUUM | Retention limits how far time travel reaches |
| Time travel | Delta time travel and RESTORE | Same penalty-correction demo |
| Schema evolution | Auto Loader schema evolution, mergeSchema | Same allowed versus rejected drill |
| ClickHouse and the web UI | SQL warehouse dashboards, one optional app | Warehouse is one 2X-Small |
| Marquez lineage | Unity Catalog lineage | Verify availability on Free Edition |

**Free Edition limits that shape the design** (from the [Databricks limitations page](https://docs.databricks.com/gcp/en/getting-started/free-edition-limitations), last updated Oct 18, 2026)

- One SQL warehouse, 2X-Small size; a maximum of 5 concurrent job tasks; one active Lakeflow pipeline per pipeline type.
- Up to 3 Databricks Apps, each running up to 24 hours before it must be restarted.
- Exceeding the quota shuts compute down for the rest of the day, and in extreme cases the rest of the month. Data and settings are kept.
- Accounts are for non-commercial use, have no support or SLA, and inactive accounts may be deleted.
- No access to the account console or account-level APIs. Workspace-level API access from outside is not covered on that page, so test it.

**Three ways to use it**

| Track | Shape | Pick it when |
| --- | --- | --- |
| A. Local only | The open stack from this plan | 16 GB RAM or more, and you want open-source depth |
| B. Local plus a Databricks leg | After phase 3, load the same history into Databricks and write a decision record on open versus managed | 16 GB or more, and you want both keyword sets. Adds roughly a week (estimate) |
| C. Databricks-first | Spark and Delta in the cloud; the laptop runs only light services | 8 GB RAM, or the full stack struggles. Loses Iceberg and Kafka-API keywords |

**Day-0 egress test.** Run this in a Databricks notebook before choosing a track. It has not been run yet, and the host names should be checked against each provider's docs:

```python
import socket
for host in ['openf1.org', 'api.jolpi.ca', 'github.com']:
    try:
        print(host, '->', socket.gethostbyname(host))
    except Exception as e:
        print(host, '-> BLOCKED:', e)
```

| Result | Consequence |
| --- | --- |
| APIs resolve | The Job can fetch data itself. Track C works end to end |
| APIs blocked, but file upload works | Use the GitHub Actions fallback |
| Both fail | Use track A and keep Databricks as a small side exercise |

**What the track adds to the resume:** Databricks, Unity Catalog, Auto Loader, Lakeflow pipelines, Delta schema evolution, time travel, MERGE, OPTIMIZE and VACUUM, plus an open-versus-managed comparison that shows judgment rather than tool familiarity.

## Laptop and environment

The laptop is a Windows x64 machine. RAM, CPU cores, free disk and virtualization status are not yet known, and they decide which profile to run. Check them in PowerShell:

```
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
Get-PSDrive C | Select-Object Free
```

Also open Task Manager, then Performance, then CPU, and confirm that Virtualization shows Enabled.

**Windows setup**

- Run everything through WSL2 and Docker Desktop. Running Spark natively on Windows is painful.
- Keep project files inside the WSL filesystem, not under /mnt/c, because file access is much faster there.
- Cap WSL memory with a .wslconfig file so Docker cannot take all of the RAM.
- Docker Desktop is believed to be free for personal use; check the current license terms.

**Approximate memory per service (measure with docker stats)**

| Service | Approx. RAM |
| --- | --- |
| Spark (driver and one worker) | 2 to 3 GB |
| Airflow (LocalExecutor, all components) | 3 to 4 GB |
| Superset (optional) | 1.5 to 2 GB |
| Marquez with its database | about 1 GB |
| Polaris | 0.5 to 1 GB |
| Redpanda | 0.5 to 1 GB, configurable |
| MinIO, Postgres | under 0.5 GB each |

**Profiles by laptop RAM**

| RAM | Profile | What to run |
| --- | --- | --- |
| 8 GB | Lean, or the Databricks track | Redpanda, MinIO, JDBC catalog, Spark only when streaming, DuckDB, Airflow, Postgres as the serving fallback in place of ClickHouse, a light dashboard (Evidence or Streamlit). Skip Superset, Marquez and the static demo build |
| 16 GB | Full, in groups | Use Docker Compose profiles (batch, streaming, serving) and start one group at a time |
| 32 GB | Full | All services together |

Keep 30 GB or more of free disk as a rough guide, and limit telemetry to a few sessions. ClickHouse memory use has not been measured, so add it to the docker stats check and set a container memory limit.

**Memory check for 16 GB:** with WSL overhead the whole stack could reach roughly 10 to 12 GB if everything ran at once (estimate), so always run Compose profiles in groups (batch, streaming, serving) and never all together.

## Risks and assumptions to verify

Check the items marked first before writing pipeline code.

| Risk or assumption | Impact | Mitigation or check |
| --- | --- | --- |
| DuckDB and dbt writing to Iceberg may be immature | Blocks the transform layer | Write with Spark or PyIceberg, read with DuckDB. Prove one write and one read in phase 0 |
| Polaris setup and auth are fiddly | Stalls phase 0 | Start with a JDBC catalog; fall back to Lakekeeper or Nessie |
| MinIO license or packaging may have changed | Setup friction | Check before building; SeaweedFS or Garage as fallback |
| Real-time OpenF1 access is believed paid | No live stream | Replay recorded sessions; confirm current terms |
| API rate limits | Slow or failed backfills | Cache raw responses, use an Airflow pool |
| Data terms of the three sources | Legal exposure | Read each license; add unofficial fan-project disclaimer |
| Laptop RAM unknown | Stack may not fit | Run the check above and pick a profile |
| Airflow memory footprint | Crowds out Spark | LocalExecutor only; start services in groups |
| Windows file I/O through /mnt/c | Slow tests and builds | Keep the repo inside WSL |
| Scope creep | Project never finishes | Core is phases 0 to 4; Trino, Marquez, Superset and the ML extension are stretch |
| Unmeasured resume numbers | Credibility | Only use figures from the benchmark report |

## Resume mapping and interview material

The project adds these keywords that the current resume does not carry: Apache Iceberg, REST catalog (Polaris), MinIO and S3-compatible object storage, Kafka and Redpanda, schema registry, Spark Structured Streaming, watermarking, partition evolution, compaction, snapshot expiry, DuckDB, OpenLineage, Superset, FastAPI, a React web UI, Kimball dimensional modeling, ClickHouse, Docker Compose and GitHub Actions. Apache Airflow and dbt already appear on the resume, so here they show deeper use rather than new names.

**Resume bullets (fill the brackets only after measuring)**

- Built a self-hosted open lakehouse (MinIO, Apache Iceberg, REST catalog) ingesting batch and streamed Formula 1 timing data, with Kafka-API streaming and Spark Structured Streaming handling late-arriving events.
- Reduced scanned data by \[X\]% and file count by \[Y\]% through compaction, partition evolution and snapshot expiry, validated by a repeatable benchmark.
- Orchestrated \[N\] DAGs in Airflow using asset-aware scheduling, dynamic task mapping and sensors, with data-quality gates in dbt and lineage emitted through OpenLineage.
- Served one Iceberg table to two engines (Spark and DuckDB) and documented \[N\] architecture decision records covering format, catalog and engine trade-offs.

**Decision records to write**

1. Iceberg versus Delta, given prior Delta experience.
2. Replayed stream versus a live feed.
3. When DuckDB is enough and when Spark or Trino is needed.
4. Retention: time-travel depth against storage cost.
5. Schema-change policy: what is automatic and what needs review.
6. Airflow versus Dagster for this workload.
7. Why dashboards read from ClickHouse and not from the lake, and why Postgres is kept only for metadata.
8. What changes at 100x data volume.

**Questions this prepares you to answer**

- Why a table format on top of Parquet, and what does a catalog do?
- How do you handle late or duplicated events in a stream?
- How do you keep a streaming job from creating thousands of small files?
- What is the difference between snapshot diffing and true change data capture?
- How would you prove which data a report was built from, months later?

## Next steps and decisions needed

Three checks and decisions come first; phase 0 can start as soon as the first is answered.

- [ ] Run the PowerShell check and note RAM, cores, free disk and virtualization status. This picks the profile.
- [ ] Optional, later: run the egress test in a Databricks notebook (see the alternative track) only if you add the Databricks leg.
- [ ] Track decided: local open stack first (phases 0 to 4). The Databricks leg is optional and comes after phase 3.
- [ ] Create the repository with the folder layout, a Makefile and the CI skeleton.
- [ ] Phase 0: bring up MinIO and a catalog, write one Iceberg table with Spark or PyIceberg, read it with DuckDB.

Once the track is chosen, the next deliverable is a day-by-day checklist for phases 0 and 1, with the Docker Compose service list for the chosen profile.

## Sources

- [race-calls README](https://github.com/herambbbb/race-calls): used for the data-source details (Jolpica, OpenF1, f1db) and the 30-minute OpenF1 history delay.
- [Databricks Free Edition limitations](https://docs.databricks.com/gcp/en/getting-started/free-edition-limitations): opened; source for the Free Edition limits in the alternative track (page updated Oct 18, 2026).
- [Databricks community thread on outbound network access](https://community.databricks.com/t5/databricks-free-edition-help/whitelist-for-outbound-network-access/m-p/146636): seen in search results, not opened; basis for the statement that no allowed-domain list is published.
- Indeed senior data engineer postings read on 2026-10-26 (Software Mechanics, HPE, LSEG, Mastercard, Madhjyoti): basis for the track decision in the debate section; a tiny, non-random sample.
- Tool behaviour, memory figures and effort estimates elsewhere in this plan are from memory and labelled approximate; verify them before relying on them.
