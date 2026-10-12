"""Commands are dispatched to the visible shell, never to a busy program."""

import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from terminal import TerminalBusy, TerminalUnavailable


def test_origin_rejection_logs_addresses_without_request_secrets(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    sent: list[str] = []
    client = TestClient(create_app(tmp_path, run_terminal=sent.append), base_url="http://internal:8081")
    with caplog.at_level(logging.WARNING, logger="workshop.origin"):
        response = client.post(
            "/api/terminal/run",
            json={"command": "echo private-command"},
            headers={
                "Origin": "https://workshop.example",
                "Sec-Fetch-Site": "same-origin",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "workshop.example",
                "Authorization": "Bearer private-token",
                "Cookie": "session=private-cookie",
            },
        )
    assert response.status_code == 403
    assert not sent
    record = next(record for record in caplog.records if record.name == "workshop.origin")
    details = json.loads(record.getMessage().split("Terminal origin rejected: ", 1)[1])
    assert details == {
        "backend_origin": "http://internal:8081",
        "browser_origin": "https://workshop.example",
        "sec_fetch_site": "same-origin",
        "forwarded_proto": "https",
        "forwarded_host": "workshop.example",
    }
    assert response.json()["diagnostics"] == details
    assert response.json()["detail"] == "Terminal commands require the same workshop origin."
    for secret in ("private-command", "private-token", "private-cookie"):
        assert secret not in response.text
    assert "private-command" not in caplog.text
    assert "private-token" not in caplog.text
    assert "private-cookie" not in caplog.text


def test_terminal_route_exists_before_runtime_is_available(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).post(
        "/api/terminal/run", json={"command": "echo hello"},
        headers={"Origin": "https://evil.test"},
    )
    assert response.status_code == 403


@pytest.fixture
def terminal_client(tmp_path: Path) -> tuple[TestClient, list[str]]:
    sent: list[str] = []
    application = create_app(tmp_path, run_terminal=sent.append)
    return TestClient(application), sent


def test_sends_exact_multiline_command_to_terminal(
    terminal_client: tuple[TestClient, list[str]],
) -> None:
    client, sent = terminal_client
    command = "printf 'café\\n'\nprintf '%s\\n' \"$PWD\"\n"
    response = client.post(
        "/api/terminal/run", json={"command": command},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    assert sent == [command]


@pytest.mark.parametrize("body", [
    {}, {"command": 1}, {"command": None}, {"command": ""},
    {"command": " \n\t"}, {"command": "echo x", "extra": True},
    {"command": "x" * 8193}, {"command": "🐍" * 3000},
    {"command": "echo x\x00"}, {"command": "echo x\r"},
    {"command": "echo x\x1b[A"}, {"command": "echo x\x7f"},
    {"command": "echo x\u0085"}, {"command": "\ud800"},
])
def test_rejects_invalid_commands_before_dispatch(
    terminal_client: tuple[TestClient, list[str]], body: object,
) -> None:
    client, sent = terminal_client
    response = client.post(
        "/api/terminal/run", content=json.dumps(body),
        headers={"Origin": "http://testserver", "Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert not sent


@pytest.mark.parametrize("headers,status", [
    ({"Origin": "https://evil.test"}, 403),
    ({"Origin": "null"}, 403),
    ({}, 403),
    ({"Origin": "http://testserver", "Sec-Fetch-Site": "cross-site"}, 403),
    ({"Origin": "http://testserver", "Content-Type": "text/plain"}, 415),
])
def test_requires_same_origin_and_json(
    terminal_client: tuple[TestClient, list[str]], headers: dict[str, str], status: int,
) -> None:
    client, sent = terminal_client
    response = client.post(
        "/api/terminal/run", content='{"command":"echo hello"}',
        headers={"Content-Type": "application/json", **headers},
    )
    assert response.status_code == status
    assert not sent


def test_origin_includes_the_public_port(terminal_client: tuple[TestClient, list[str]]) -> None:
    client, sent = terminal_client
    response = client.post(
        "http://localhost:8080/api/terminal/run", json={"command": "echo hello"},
        headers={"Origin": "http://localhost:8080"},
    )
    assert response.status_code == 200
    assert sent == ["echo hello"]


@pytest.mark.parametrize("error,status", [
    (TerminalBusy("Terminal has unfinished input."), 409),
    (TerminalUnavailable("Terminal did not confirm the command."), 503),
])
def test_reports_busy_and_failed_dispatch(tmp_path: Path, error: Exception, status: int) -> None:
    def fail(_command: str) -> None:
        raise error

    client = TestClient(create_app(tmp_path, run_terminal=fail))
    response = client.post(
        "/api/terminal/run", json={"command": "echo hello"},
        headers={"Origin": "http://testserver"},
    )
    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


def test_rejects_malformed_json(terminal_client: tuple[TestClient, list[str]]) -> None:
    client, sent = terminal_client
    response = client.post(
        "/api/terminal/run", content='{"command":',
        headers={"Origin": "http://testserver", "Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert not sent
