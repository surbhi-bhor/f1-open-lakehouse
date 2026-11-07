"""Read an Iceberg table with DuckDB, finding its current metadata file through the catalog."""

import re
from urllib.parse import urlparse

import duckdb
import psycopg

from f1lake.config import Settings, load_settings

_COLUMN = re.compile(r"^[a-z_]+$")


def metadata_location(s: Settings, namespace: str, table: str) -> str:
    # shortcut: reads the JDBC catalog table directly; replace with a REST catalog client when moving to Polaris/Lakekeeper in phase 3
    with psycopg.connect(
        host=s.pg_host, port=s.pg_port, user=s.pg_user, password=s.pg_password,
        dbname=s.pg_catalog_db,
    ) as conn:
        row = conn.execute(
            "SELECT metadata_location FROM iceberg_tables"
            " WHERE catalog_name = %s AND table_namespace = %s AND table_name = %s",
            (s.catalog_name, namespace, table),
        ).fetchone()
    if row is None:
        raise LookupError(f"{s.catalog_name}.{namespace}.{table} is not in the catalog")
    return row[0]


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def read_table(s: Settings, namespace: str, table: str, columns: list[str]) -> list[tuple]:
    for c in columns:
        if not _COLUMN.match(c):
            raise ValueError(f"bad column name: {c!r}")
    location = metadata_location(s, namespace, table)
    con = duckdb.connect()
    try:
        con.execute("INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs")
        # CREATE SECRET takes no bound parameters, so values are quoted as literals.
        con.execute(
            "CREATE SECRET (TYPE s3, KEY_ID " + _literal(s.s3_access_key)
            + ", SECRET " + _literal(s.s3_secret_key)
            + ", ENDPOINT " + _literal(urlparse(s.s3_endpoint).netloc)
            + ", URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')"
        )
        return con.execute(
            f"SELECT {', '.join(columns)} FROM iceberg_scan(?) ORDER BY 1", [location]
        ).fetchall()
    finally:
        con.close()


if __name__ == "__main__":
    for r in read_table(load_settings(), "bronze", "smoke_drivers", ["driver_id", "code", "season"]):
        print(r)
