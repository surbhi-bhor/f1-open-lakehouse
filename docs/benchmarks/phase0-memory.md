# Phase 0 memory measurement

Measured on 2026-11-07, from Ubuntu (WSL2) in the repo folder. Only measured values are listed here.

## Machine

| Item | Value |
| --- | --- |
| RAM | 15.8 GB (Windows) |
| CPU | i7-1195G7, 8 logical processors |
| Memory WSL sees (`free -h`, total) | 6.8 GiB |
| Docker | server 29.9.2, Docker Desktop on WSL 2.7.11 |
| Other load | Chrome and Brave closed; the content-intelligence pipeline stopped |

The 6.8 GiB WSL total is lower than the 10 GB that `.wslconfig` was set to in Task 0. That gap is not explained yet. Check `.wslconfig` before phase 1 adds Airflow.

## Commands

```bash
make up
make stats                       # idle
make smoke-write &               # second shell in the plan; a background job here
docker stats --no-stream ...     # sampled about every 2 s while smoke-write ran
make stats                       # right after
free -h
```

Stack: `apache/spark:3.5.7-java17-python3` (`local[2]`, `--driver-memory 2g`), `postgres:16.15`, MinIO `RELEASE.2025-10-15T17-29-55Z`. Iceberg 1.12.0. The Ivy jar cache was already warm.

## Results (MEM USAGE / mem_limit)

| Moment | spark | postgres | minio | WSL available |
| --- | --- | --- | --- | --- |
| Idle, after `make up` | 560 KiB / 3 GiB | 20.0 MiB / 512 MiB | 63.6 MiB / 512 MiB | 5.7 GiB |
| During `smoke-write`, peak sample | 831.2 MiB / 3 GiB (27%) | 24.8 MiB / 512 MiB (5%) | 68.4 MiB / 512 MiB (13%) | 5.1 GiB (5212 MiB) |
| Right after | 1.5 MiB / 3 GiB | 21.8 MiB / 512 MiB | 67.1 MiB / 512 MiB | 5.7 GiB |

`smoke-write` took about 16 s from submit to exit with a warm jar cache. Spark memory climbed steadily, by about 100 MiB every 2 s, until the job ended, so the true peak may be a little above the last sample.

## Verdict

No service came within 10% of its `mem_limit`, so no limit changes. Spark's 3 GiB cap leaves a lot of headroom for the three-row smoke job. Phase 1 needs a real-sized load measured before anyone lowers it.
