from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_gitattributes_forces_lf():
    # Windows checkouts would otherwise turn bash scripts and the Makefile into CRLF.
    assert "* text=auto eol=lf" in (ROOT / ".gitattributes").read_text().splitlines()
