import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from urllib.request import urlopen

_MODULE_DIR = Path(__file__).resolve().parent
_CACHE_DIR = (_MODULE_DIR.parent if _MODULE_DIR.name == "solutions" else _MODULE_DIR) / "cached_docs"
# URL fragment -> cached file, used as a fallback if the live fetch fails.
_DOC_CACHE = {"fastapi.tiangolo.com": "fastapi.md"}
_SKIP_DIRS = {".git", ".pytest_cache", ".venv", "__pycache__", "node_modules"}
MAX_OUTPUT_CHARS = 6000
MAX_READ_LINES = 80
MAX_FILES = 200


def _default_fetcher(url: str) -> str:
    try:
        with urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        for fragment, fname in _DOC_CACHE.items():
            if fragment in url:
                with open(os.path.join(_CACHE_DIR, fname)) as f:
                    return f.read()
        raise


def web_fetch(
    url: str, limit: int = MAX_OUTPUT_CHARS, fetcher: Callable[[str], str] | None = None
) -> str:
    """Prebuilt; implementing this is an optional extension after the core lab."""
    if not 1 <= limit <= MAX_OUTPUT_CHARS:
        raise ValueError(f"limit must be between 1 and {MAX_OUTPUT_CHARS}")
    text = (fetcher or _default_fetcher)(url)
    if len(text) > limit:
        return text[:limit] + f"\n... [truncated, {len(text)} chars total]"
    return text


def str_replace(path: str, old_str: str, new_str: str) -> str:
    with open(path) as f:
        content = f.read()
    count = content.count(old_str)
    if count == 0:
        raise ValueError(f"old_str not found in {path}")
    if count > 1:
        raise ValueError(
            f"old_str is not unique: found {count} times in {path}. "
            "Include more surrounding context to make it unique."
        )
    updated = content.replace(old_str, new_str)
    with open(path, "w") as f:
        f.write(updated)
    return f"Edited {path}"


def file_excerpt(text: str, offset: int = 1, limit: int = MAX_READ_LINES) -> str:
    """Provided formatting: line numbers, a context budget, and continuation hints."""
    if offset < 1 or not 1 <= limit <= MAX_READ_LINES:
        raise ValueError(f"offset must be positive; limit must be 1..{MAX_READ_LINES}")
    lines = text.splitlines()
    if not lines:
        return "(empty file)"
    if offset > len(lines):
        return f"(offset {offset} is past end; {len(lines)} lines total)"
    page: list[str] = []
    size = 0
    for index in range(offset - 1, min(len(lines), offset - 1 + limit)):
        numbered = f"{index + 1}: {lines[index]}"
        if size + len(numbered) + 1 > MAX_OUTPUT_CHARS:
            if not page:
                return numbered[:MAX_OUTPUT_CHARS] + (
                    f"\n... [truncated within line {index + 1}; use a targeted shell "
                    "command to inspect a column range of this long line]"
                )
            break
        page.append(numbered)
        size += len(numbered) + 1
    result = "\n".join(page)
    next_offset = offset + len(page)
    if next_offset <= len(lines):
        result += f"\n... [truncated; {len(lines)} lines total; continue with offset={next_offset}]"
    return result


def read_file(path: str, offset: int = 1, limit: int = MAX_READ_LINES) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return file_excerpt(text, offset, limit)


def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


def list_files(path: str = ".") -> str:
    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {path}")
    paths: list[str] = []
    size = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
        for fname in sorted(files):
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, directory)
            if len(paths) >= MAX_FILES or size + len(rel_path) + 1 > MAX_OUTPUT_CHARS:
                return "\n".join(paths) + "\n... [truncated; choose a more specific subdirectory]"
            paths.append(rel_path)
            size += len(rel_path) + 1
    return "\n".join(paths) if paths else "(no files found)"


def run_bash(command: str, timeout: int = 60) -> str:
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=timeout
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if len(out) > MAX_OUTPUT_CHARS:
        out = out[-MAX_OUTPUT_CHARS:] + (
            f"\n... [truncated; showing last {MAX_OUTPUT_CHARS} of {len(out)} characters; "
            "narrow the command for more detail]"
        )
    return f"exit {proc.returncode}\n{out}".strip()


# ---------------------------------------------------------------------------
# Tool schemas (sent to the model) and the name -> function registry.
# The six tools the agent can call. run_bash and web_fetch are gated in the UI.
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Discover project files, skipping generated folders. Returns up to 200 paths. Use a narrower path if truncated; use read_file to inspect a known file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Inspect a known UTF-8 file. Returns numbered lines with a bounded character budget. Use offset and limit for pages; follow truncation guidance. Use list_files to discover paths and str_replace to edit. Example: path='app.py', offset=1, limit=40.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer", "minimum": 1, "description": "First line, 1-based; default 1"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 80, "description": "Maximum lines; default 80"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace an exact, unique string in a file. old_str must occur "
                "exactly once; include surrounding context to make it unique."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {"type": "string"},
                    "new_str": {"type": "string"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Run tests, scripts, and servers in the working directory. Requires runtime approval. Returns exit code and the last 6000 output characters. Prefer read_file for known file contents and list_files for discovery. Background servers with output redirected to a log.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch a URL and return its (truncated) text content.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]

REGISTRY = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "run_bash": run_bash,
    "web_fetch": web_fetch,
}

# Tools that hand real power to the model — require human approval before running.
GATED = {"run_bash", "web_fetch"}
