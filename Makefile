.PHONY: lint test check compose-config up down ps stats

# The repo sits on the Windows drive; a Linux venv inside it breaks, so keep it in WSL's home.
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/f1lake

# Pinned versions live in .env.example; a local .env overrides them.
include .env.example
-include .env

COMPOSE := docker compose --profile batch
ICEBERG_PACKAGES := org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:$(ICEBERG_VERSION),org.apache.iceberg:iceberg-aws-bundle:$(ICEBERG_VERSION),org.postgresql:postgresql:$(PG_JDBC_VERSION)
SPARK_SUBMIT := $(COMPOSE) exec spark /opt/spark/bin/spark-submit --master local[2] --driver-memory 2g --conf spark.jars.ivy=/opt/ivy --packages $(ICEBERG_PACKAGES)

.env:
	cp -n .env.example .env

lint:
	uv run ruff check .

test:
	uv run pytest

compose-config: .env
	$(COMPOSE) config -q

check: lint test compose-config

up: .env
	$(COMPOSE) up -d --wait

# Keeps the data volumes; `docker compose down -v` would delete the lake.
down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps -a

stats:
	docker stats --no-stream
