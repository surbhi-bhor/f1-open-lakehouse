import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
SERVICES = yaml.safe_load((ROOT / "docker-compose.yml").read_text())["services"]
ENV_EXAMPLE = dict(
    line.split("=", 1) for line in (ROOT / ".env.example").read_text().splitlines()
    if line and not line.startswith("#"))


def test_every_service_has_mem_limit():
    missing = [name for name, svc in SERVICES.items() if "mem_limit" not in svc]
    assert missing == []


def _expand(value: str) -> str:
    def lookup(m: re.Match) -> str:
        assert m[1] in ENV_EXAMPLE, f"{m[1]} missing from .env.example"
        return ENV_EXAMPLE[m[1]]
    return re.sub(r"\$\{(\w+)\}", lookup, value)


def test_no_image_uses_latest_tag():
    for name, svc in SERVICES.items():
        image = _expand(svc["image"])
        repo, _, tag = image.rpartition(":")
        assert repo and tag and tag != "latest", f"{name}: unpinned image {image}"


def test_minio_build_is_pinned_to_commits():
    for key in ("MINIO_COMMIT", "MC_COMMIT"):
        assert re.fullmatch(r"[0-9a-f]{40}", ENV_EXAMPLE[key]), f"{key} must be a full commit SHA"
    workflow = (ROOT / ".github/workflows/minio-image.yml").read_text()
    assert "MINIO_COMMIT=${{ env.MINIO_COMMIT }}" in workflow
    assert "MC_COMMIT=${{ env.MC_COMMIT }}" in workflow


def test_spark_only_in_profiles():
    assert SERVICES["spark"]["profiles"] == ["batch", "streaming"]
    assert "profiles" not in SERVICES["minio"]
    assert "profiles" not in SERVICES["postgres"]


def test_ports_bound_to_localhost_only():
    for name, svc in SERVICES.items():
        for port in svc.get("ports", []):
            assert port.startswith("127.0.0.1:"), f"{name}: {port} is reachable from the network"


def test_env_file_is_gitignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()
