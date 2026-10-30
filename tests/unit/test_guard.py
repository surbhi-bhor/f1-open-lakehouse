import subprocess
from pathlib import Path

GUARD = Path(__file__).parents[2] / "scripts" / "guard_location.sh"


def run_guard(directory: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(GUARD), directory],
                          check=False, capture_output=True, text=True)


def test_guard_rejects_mnt_c():
    r = run_guard("/mnt/c/x")
    assert r.returncode == 1
    assert "inside the WSL filesystem" in r.stderr


def test_guard_accepts_home():
    assert run_guard("/home/u/f1-open-lakehouse").returncode == 0
