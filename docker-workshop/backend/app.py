import errno
import json
import os
import stat
from collections.abc import Awaitable, Callable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Annotated, BinaryIO, Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from terminal import TerminalBusy, TerminalDispatcher, TerminalUnavailable

MAX_CONTENT_BYTES = 1024 * 1024
EXCLUDED_DIRECTORIES = {"node_modules", "__pycache__", "dist", "build"}
LANGUAGES = {
    ".py": "python",
    ".toml": "toml",
    ".md": "markdown",
    ".txt": "plaintext",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "shell",
    ".html": "html",
    ".css": "css",
    ".js": "javascript",
    ".ts": "typescript",
}


class Health(BaseModel):
    status: Literal["ok"] = "ok"


class RunCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: StrictStr = Field(min_length=1, max_length=8192)

    @field_validator("command")
    @classmethod
    def validate_command(cls, command: str) -> str:
        if not command.strip() or len(command.encode("utf-8")) > 8192:
            raise ValueError("Command must contain text and must not exceed 8192 UTF-8 bytes.")
        if any((ord(char) < 32 or 127 <= ord(char) <= 159) and char not in "\n\t" for char in command):
            raise ValueError("Command cannot contain terminal control characters.")
        return command


class CommandSent(BaseModel):
    status: Literal["sent"] = "sent"


class FileSummary(BaseModel):
    name: str
    path: str
    language: str


class FileContent(BaseModel):
    path: str
    content: str
    language: str


class SaveFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: StrictStr = Field(min_length=1, max_length=4096)
    content: StrictStr = Field(max_length=MAX_CONTENT_BYTES)

    @field_validator("content")
    @classmethod
    def validate_content_size(cls, content: str) -> str:
        if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError("File content must not exceed 1 MiB in UTF-8.")
        return content


def is_hidden_or_generated(name: str) -> bool:
    return name.startswith(".") or name in EXCLUDED_DIRECTORIES


def checked_file(root: Path, path: str) -> Path:
    """Resolve an existing editable file without allowing symlink traversal."""
    relative = Path(path)
    if "\x00" in path or "\\" in path:
        raise HTTPException(400, "Invalid file path.")
    if relative.is_absolute() or ".." in relative.parts:
        raise HTTPException(403, "File path must stay inside the workspace.")
    if any(is_hidden_or_generated(part) for part in relative.parts):
        raise HTTPException(403, "Hidden and generated files cannot be edited.")
    if relative.suffix.lower() not in LANGUAGES:
        raise HTTPException(403, "This file type cannot be edited.")

    try:
        candidate = root
        for part in relative.parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise HTTPException(403, "Symbolic links cannot be edited.")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise HTTPException(403, "File path must stay inside the workspace.")
        if not resolved.is_file():
            raise HTTPException(404, "File not found.")
    except PermissionError as error:
        raise HTTPException(403, "File path is not accessible.") from error
    except (OSError, UnicodeError) as error:
        raise HTTPException(400, "Invalid file path.") from error
    return resolved


@contextmanager
def open_file(
    root: Path, path: str, *, writable: bool = False
) -> Iterator[tuple[Path, BinaryIO]]:
    file = checked_file(root, path)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        with ExitStack() as resources:
            directory_fd = os.open(root, directory_flags)
            resources.callback(os.close, directory_fd)
            parts = Path(path).parts
            for part in parts[:-1]:
                directory_fd = os.open(part, directory_flags, dir_fd=directory_fd)
                resources.callback(os.close, directory_fd)

            access_flags = os.O_RDWR if writable else os.O_RDONLY
            file_fd = os.open(
                parts[-1], access_flags | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fd,
            )
            stream = resources.enter_context(os.fdopen(file_fd, "r+b" if writable else "rb"))
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise HTTPException(403, "Only regular files can be edited.")
            # Traverse with directory descriptors and never reopen by pathname.
            yield file, stream
    except FileNotFoundError as error:
        raise HTTPException(404, "File not found.") from error
    except PermissionError as error:
        raise HTTPException(403, "File is not accessible.") from error
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise HTTPException(403, "Symbolic links cannot be edited.") from error
        raise HTTPException(400, "Unable to access file.") from error


def read_content(stream: BinaryIO) -> str:
    content = stream.read(MAX_CONTENT_BYTES + 1)
    if len(content) > MAX_CONTENT_BYTES:
        raise HTTPException(400, "File content must not exceed 1 MiB.")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(400, "Only UTF-8 text files can be edited.") from error


def create_app(
    workspace: Path | None = None,
    *,
    run_terminal: Callable[[str], None] | None = None,
) -> FastAPI:
    configured_root = (
        workspace
        if workspace is not None
        else Path(os.getenv("WORKSPACE_ROOT", "/workspace"))
    )
    root = configured_root.resolve()
    application = FastAPI(title="Workshop editor")
    dispatch = run_terminal or TerminalDispatcher().run

    @application.middleware("http")
    async def protect_terminal(
        request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/api/terminal/run" and request.method == "POST":
            origin = f"{request.url.scheme}://{request.url.netloc}"
            if (
                request.headers.get("origin") != origin
                or request.headers.get("sec-fetch-site", "same-origin") != "same-origin"
            ):
                return Response(
                    content='{"detail":"Terminal commands require the same workshop origin."}',
                    status_code=403, media_type="application/json",
                )
            if request.headers.get("content-type", "").split(";", 1)[0].lower() != "application/json":
                return Response(
                    content='{"detail":"Terminal commands require application/json."}',
                    status_code=415, media_type="application/json",
                )
        return await call_next(request)

    @application.post("/api/terminal/run")
    def run_command(request: RunCommand) -> CommandSent:
        try:
            dispatch(request.command)
        except TerminalBusy as error:
            raise HTTPException(409, str(error)) from error
        except (TerminalUnavailable, OSError) as error:
            raise HTTPException(503, str(error)) from error
        return CommandSent()

    @application.exception_handler(RequestValidationError)
    async def invalid_request(
        _request: Request, error: RequestValidationError
    ) -> Response:
        # Invalid Unicode may appear in validation details; escape it for JSON.
        return Response(
            content=json.dumps(
                {"detail": jsonable_encoder(error.errors())}, ensure_ascii=True
            ),
            status_code=422,
            media_type="application/json",
        )

    @application.get("/api/health")
    def health() -> Health:
        return Health()

    @application.get("/api/editor/files")
    def list_files() -> list[FileSummary]:
        if not root.is_dir():
            raise HTTPException(404, "Workspace directory not found.")
        files: list[FileSummary] = []

        def directory_error(error: OSError) -> None:
            raise HTTPException(403, "Unable to list workspace directory.") from error

        for directory, directories, filenames in os.walk(root, onerror=directory_error):
            parent = Path(directory)
            directories[:] = [
                name
                for name in directories
                if not is_hidden_or_generated(name) and not (parent / name).is_symlink()
            ]
            for name in filenames:
                file = parent / name
                if (
                    is_hidden_or_generated(name)
                    or file.is_symlink()
                    or file.suffix.lower() not in LANGUAGES
                ):
                    continue
                path = file.relative_to(root).as_posix()
                try:
                    with open_file(root, path) as (_, stream):
                        read_content(stream)
                except HTTPException as error:
                    if error.status_code == 400:
                        continue  # Binary and oversized files are not editable text.
                    raise
                files.append(
                    FileSummary(
                        name=name, path=path, language=LANGUAGES[file.suffix.lower()]
                    )
                )
        return sorted(files, key=lambda file: file.path)

    @application.get("/api/editor/file")
    def get_file(path: Annotated[str, Query(min_length=1, max_length=4096)]) -> FileContent:
        with open_file(root, path) as (file, stream):
            content = read_content(stream)
        return FileContent(
            path=file.relative_to(root).as_posix(),
            content=content,
            language=LANGUAGES[file.suffix.lower()],
        )

    @application.post("/api/editor/file")
    def save_file(request: SaveFile) -> FileContent:
        with open_file(root, request.path, writable=True) as (file, stream):
            read_content(stream)
            stream.seek(0)
            stream.write(request.content.encode("utf-8"))
            stream.truncate()
        return FileContent(
            path=file.relative_to(root).as_posix(),
            content=request.content,
            language=LANGUAGES[file.suffix.lower()],
        )

    return application


app = create_app()
