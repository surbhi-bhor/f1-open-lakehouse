-- Runs once, on the first start of an empty data volume. Postgres holds bookkeeping only, never F1 data.
CREATE DATABASE iceberg_catalog;
CREATE DATABASE airflow;  -- reserved for phase 1
