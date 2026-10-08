"""First tool: real files, before adding output budgets and paging."""

from pathlib import Path

import pytest

from tools import read_file


def test_read_file_returns_the_file_text(tmp_path: Path) -> None:
    path = tmp_path / "brief.txt"
    path.write_text("Ship a café task board.", encoding="utf-8")
    assert "Ship a café task board." in read_file(str(path))


def test_missing_file_raises_for_the_harness_to_handle(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_file(str(tmp_path / "missing.txt"))
