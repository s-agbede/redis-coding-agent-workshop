import json
import logging
import os
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from terminal import TerminalBusy, TerminalDispatcher, TerminalUnavailable

origin_logger = logging.getLogger("workshop.origin")
# Match the entire canonical origin: no credentials, ports, paths or suffixes.
# The fixed hostname prefix uses 17 of a DNS label's maximum 63 characters.
LABS_ORIGIN = re.compile(r"https://8080-p-rl-s-labs-[a-z0-9]{1,46}\.labs\.ps-redis\.com")


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
    application = FastAPI(title="Workshop runtime")
    dispatch = run_terminal or TerminalDispatcher().run

    @application.middleware("http")
    async def protect_terminal(
        request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/api/terminal/run" and request.method == "POST":
            origin = f"{request.url.scheme}://{request.url.netloc}"
            browser_origin = request.headers.get("origin")
            fetch_site = request.headers.get("sec-fetch-site")
            exact_origin = browser_origin == origin and fetch_site in (None, "same-origin")
            # Labs rewrites Host/scheme. Require explicit browser metadata for
            # this fallback; missing metadata is accepted only by the exact check.
            hosted_origin = (
                fetch_site == "same-origin"
                and LABS_ORIGIN.fullmatch(browser_origin or "") is not None
            )
            if not (exact_origin or hosted_origin):
                # Share only bounded address metadata, never commands, cookies or credentials.
                details = {
                    "backend_origin": origin,
                    "browser_origin": request.headers.get("origin"),
                    "sec_fetch_site": request.headers.get("sec-fetch-site"),
                    "forwarded_proto": request.headers.get("x-forwarded-proto"),
                    "forwarded_host": request.headers.get("x-forwarded-host"),
                }
                diagnostics = {
                    key: value[:512] if value is not None else None
                    for key, value in details.items()
                }
                origin_logger.warning("Terminal origin rejected: %s", json.dumps(diagnostics))
                return Response(
                    content=json.dumps({
                        "detail": "Terminal commands require the same workshop origin.",
                        "diagnostics": diagnostics,
                    }),
                    status_code=403, media_type="application/json",
                    headers={"Cache-Control": "no-store"},
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

    @application.get("/api/preview")
    def preview_status() -> dict[str, str]:
        ready = Path(os.getenv("WORKSHOP_PREVIEW_FILE", "/tmp/workshop-preview")).with_suffix(".ready")
        if not ready.is_file():
            raise HTTPException(503, "App Preview is starting.")
        return json.loads(ready.read_text())

    return application


app = create_app()
