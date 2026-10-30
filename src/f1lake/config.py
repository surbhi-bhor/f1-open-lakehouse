"""Connection settings shared by every engine, so Spark and DuckDB cannot drift apart."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    pg_host: str
    pg_port: int
    pg_user: str
    pg_password: str
    pg_catalog_db: str = "iceberg_catalog"
    warehouse: str = "s3://warehouse/"
    catalog_name: str = "lake"


def _required(env: Mapping[str, str], name: str) -> str:
    # An empty secret must fail here, not later as a confusing auth error.
    if not env.get(name):
        raise KeyError(f"{name} is not set; copy .env.example to .env")
    return env[name]


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    return Settings(
        s3_endpoint=env.get("S3_ENDPOINT", "http://localhost:8333"),
        s3_access_key=_required(env, "S3_ACCESS_KEY"),
        s3_secret_key=_required(env, "S3_SECRET_KEY"),
        pg_host=env.get("PG_HOST", "localhost"),
        # 5433 on the host: the content-intelligence pipeline already holds 5432.
        pg_port=int(env.get("PG_PORT", "5433")),
        pg_user=_required(env, "POSTGRES_USER"),
        pg_password=_required(env, "POSTGRES_PASSWORD"),
    )


def spark_catalog_conf(s: Settings) -> dict[str, str]:
    p = f"spark.sql.catalog.{s.catalog_name}"
    return {
        "spark.sql.extensions":
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        p: "org.apache.iceberg.spark.SparkCatalog",
        f"{p}.catalog-impl": "org.apache.iceberg.jdbc.JdbcCatalog",
        f"{p}.uri": f"jdbc:postgresql://{s.pg_host}:{s.pg_port}/{s.pg_catalog_db}",
        f"{p}.jdbc.user": s.pg_user,
        f"{p}.jdbc.password": s.pg_password,
        f"{p}.warehouse": s.warehouse,
        f"{p}.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
        f"{p}.s3.endpoint": s.s3_endpoint,
        f"{p}.s3.path-style-access": "true",
        f"{p}.s3.access-key-id": s.s3_access_key,
        f"{p}.s3.secret-access-key": s.s3_secret_key,
        # S3FileIO needs a region even though MinIO ignores it.
        f"{p}.client.region": "us-east-1",
    }
