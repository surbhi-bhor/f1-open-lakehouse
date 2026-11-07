"""Phase 0 smoke job: write three drivers into lake.bronze.smoke_drivers. Safe to re-run."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

from f1lake.config import load_settings, spark_catalog_conf

TABLE = "lake.bronze.smoke_drivers"
ROWS = [("hamilton", "HAM", 2024), ("leclerc", "LEC", 2024), ("max_verstappen", "VER", 2024)]


def main() -> None:
    builder = SparkSession.builder.appName("smoke_write")
    for key, value in spark_catalog_conf(load_settings()).items():
        builder = builder.config(key, value)
    spark = builder.getOrCreate()

    spark.sql("CREATE NAMESPACE IF NOT EXISTS lake.bronze")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            driver_id STRING, code STRING, season INT, ingested_at TIMESTAMP
        ) USING iceberg PARTITIONED BY (season)
    """)

    df = spark.createDataFrame(ROWS, "driver_id STRING, code STRING, season INT")
    # Replacing whole partitions is what makes a re-run idempotent.
    df.withColumn("ingested_at", current_timestamp()).writeTo(TABLE).overwritePartitions()

    snapshots = spark.sql(f"SELECT count(*) FROM {TABLE}.snapshots").first()[0]
    print(f"{TABLE}: {snapshots} snapshots")
    spark.stop()


if __name__ == "__main__":
    main()
