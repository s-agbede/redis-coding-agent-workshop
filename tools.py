"""Supplied file/command tools and the schemas advertised to the model."""
import os
import subprocess
from pathlib import Path

_SKIP_DIRS = {".git", ".pytest_cache", ".venv", "__pycache__", "node_modules"}
MAX_OUTPUT_CHARS = 6000
MAX_READ_LINES = 80
MAX_FILES = 200


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
    start_index = offset - 1
    end_index = min(len(lines), start_index + limit)
    for index in range(start_index, end_index):
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


def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


def list_files(path: str = ".") -> str:
    """Return paths that read_file can use from the current working directory."""
    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {path}")
    paths: list[str] = []
    size = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
        for fname in sorted(files):
            file_path = str(Path(root) / fname)
            if len(paths) >= MAX_FILES or size + len(file_path) + 1 > MAX_OUTPUT_CHARS:
                return "\n".join(paths) + "\n... [truncated; choose a more specific subdirectory]"
            paths.append(file_path)
            size += len(file_path) + 1
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


LIST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": (
            "Discover project files, skipping generated folders. Returns up to 200 paths. Use a "
            "narrower path if truncated; use read_file to inspect a known file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": []
        }
    }
}

PLAIN_READ_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the complete UTF-8 text of a known local file. Use list_files to discover paths.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    }
}

PAGED_READ_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Inspect a known UTF-8 file. Returns numbered lines with a bounded character "
            "budget. Use offset and limit for pages; follow truncation guidance. Use list_files "
            "to discover paths and str_replace to edit. Example: path='app.py', offset=1, "
            "limit=40."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "First line, 1-based; default 1"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 80,
                    "description": "Maximum lines; default 80"
                }
            },
            "required": ["path"]
        }
    }
}

WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    }
}

STR_REPLACE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "str_replace",
        "description": (
            "Replace an exact, unique string in a file. old_str must occur exactly once; "
            "include surrounding context to make it unique."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_str": {"type": "string"},
                "new_str": {"type": "string"}
            },
            "required": ["path", "old_str", "new_str"]
        }
    }
}

RUN_BASH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_bash",
        "description": (
            "Run tests, scripts, and servers in the working directory. Requires runtime "
            "approval. Returns exit code and the last 6000 output characters."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
    }
}
