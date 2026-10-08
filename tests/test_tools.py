import pytest

import shlex
import sys
import importlib
from pathlib import Path

from tools import list_files, read_file, run_bash, str_replace, web_fetch


def test_read_file_returns_numbered_page_and_next_offset(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("first\nsecond\nthird\nfourth\n")
    result = read_file(str(path), offset=2, limit=2)
    assert result.startswith("2: second\n3: third")
    assert "truncated" in result
    assert "offset=4" in result
    assert read_file(str(path), offset=4) == "4: fourth"


def test_read_file_is_bounded_even_for_a_single_huge_line(tmp_path):
    path = tmp_path / "huge.txt"
    path.write_text("A" * 20_000)
    result = read_file(str(path))
    assert len(result) < 6500
    assert "truncated" in result
    assert "column" in result


@pytest.mark.parametrize("offset,limit", [(0, 10), (-1, 10), (1, 0), (1, 81)])
def test_read_file_rejects_invalid_page(tmp_path, offset, limit):
    path = tmp_path / "notes.txt"
    path.write_text("hello")
    with pytest.raises(ValueError):
        read_file(str(path), offset=offset, limit=limit)


def test_read_file_reports_empty_file_and_offset_beyond_end(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("")
    assert read_file(str(path)) == "(empty file)"
    path.write_text("hello")
    assert "past end" in read_file(str(path), offset=2)


def test_directory_output_reports_truncation(tmp_path):
    for index in range(210):
        (tmp_path / f"file-{index:03}.txt").touch()
    result = list_files(str(tmp_path))
    assert "truncated" in result
    assert "subdirectory" in result
    assert len(result) < 6500


def test_shell_output_retains_exit_status_and_failure_tail():
    script = "print('x' * 10000); print('IMPORTANT FAILURE'); raise SystemExit(7)"
    result = run_bash(f"{shlex.quote(sys.executable)} -c {shlex.quote(script)}")
    assert result.startswith("exit 7")
    assert "IMPORTANT FAILURE" in result
    assert "truncated" in result
    assert len(result) < 6500


def test_str_replace_replaces_a_unique_match(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("def add(a, b):\n    return a - b\n")

    str_replace(str(f), "return a - b", "return a + b")

    assert f.read_text() == "def add(a, b):\n    return a + b\n"


def test_str_replace_errors_when_match_is_missing(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("def add(a, b):\n    return a + b\n")

    with pytest.raises(ValueError, match="not found"):
        str_replace(str(f), "return a - b", "return a * b")

    # The file is left untouched on failure.
    assert f.read_text() == "def add(a, b):\n    return a + b\n"


def test_str_replace_errors_when_match_is_not_unique(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\ny = 1\n")

    with pytest.raises(ValueError, match="2 times"):
        str_replace(str(f), "= 1", "= 2")

    # No edit applied when the match is ambiguous.
    assert f.read_text() == "x = 1\ny = 1\n"


def test_list_files_returns_relative_project_paths(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hi')\n")
    (tmp_path / "README.md").write_text("# demo\n")

    result = list_files(str(tmp_path))

    assert result.splitlines() == ["README.md", "app/main.py"]


@pytest.mark.parametrize("module_name", ["tools", "solutions.tools"])
def test_list_files_empty_path_lists_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module_name: str,
) -> None:
    tool_module = importlib.import_module(module_name)
    (tmp_path / "app").mkdir()
    (tmp_path / "app/main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = tool_module.list_files(path="")

    assert result.splitlines() == ["README.md", "app/main.py"]
    assert result == tool_module.list_files(path=".")


def test_list_files_skips_common_generated_directories(tmp_path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.py").write_text("nope\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "ignored.pyc").write_text("nope\n")
    (tmp_path / "agent.py").write_text("# keep\n")

    result = list_files(str(tmp_path))

    assert result == "agent.py"


def test_web_fetch_truncates_oversized_content():
    # Behavior 8: large pages are truncated so they can't blow up the context window.
    big = "A" * 10_000
    result = web_fetch("https://example.com/docs", limit=100, fetcher=lambda url: big)

    assert len(result) < len(big)
    assert result.startswith("A" * 100)
    assert "truncated" in result


def test_web_fetch_returns_short_content_unchanged():
    result = web_fetch("https://example.com", limit=100, fetcher=lambda url: "short page")

    assert result == "short page"
