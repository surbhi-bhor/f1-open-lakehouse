"""Phase 0 proof: Spark writes an Iceberg table, DuckDB reads the same table."""

import subprocess

import pytest

from f1lake.config import load_settings
from f1lake.read_duckdb import read_table

pytestmark = pytest.mark.integration

EXPECTED = [("hamilton", "HAM", 2024), ("leclerc", "LEC", 2024), ("max_verstappen", "VER", 2024)]
COLS = ["driver_id", "code", "season"]


def write() -> None:
    subprocess.run(["make", "smoke-write"], check=True)


def test_roundtrip_spark_write_duckdb_read():
    write()
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED


def test_rewrite_is_idempotent():
    write()
    write()
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED


def test_survives_restart():
    write()
    subprocess.run(["make", "down"], check=True)
    subprocess.run(["make", "up"], check=True)
    assert read_table(load_settings(), "bronze", "smoke_drivers", COLS) == EXPECTED
