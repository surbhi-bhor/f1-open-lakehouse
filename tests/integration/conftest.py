"""Load .env into os.environ so load_settings() works on the host, as `make` does."""

import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _load_env(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # Real environment wins, like docker compose does.
        os.environ.setdefault(key.strip(), value.strip())


if ENV_FILE.exists():
    _load_env(ENV_FILE)
