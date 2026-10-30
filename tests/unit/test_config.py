import pytest

from f1lake.config import load_settings, spark_catalog_conf

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
    assert conf["spark.sql.extensions"] == (
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")


def test_defaults_target_localhost():
    s = load_settings({k: v for k, v in ENV.items()
                       if k not in ("PG_HOST", "PG_PORT", "S3_ENDPOINT")})
    assert (s.pg_host, s.pg_port, s.s3_endpoint) == ("localhost", 5433, "http://localhost:9000")


def test_load_settings_missing_secret_raises():
    env = dict(ENV)
    del env["MINIO_ROOT_PASSWORD"]
    with pytest.raises(KeyError, match="MINIO_ROOT_PASSWORD"):
        load_settings(env)


def test_load_settings_empty_secret_raises():
    with pytest.raises(KeyError, match="POSTGRES_PASSWORD"):
        load_settings({**ENV, "POSTGRES_PASSWORD": ""})
