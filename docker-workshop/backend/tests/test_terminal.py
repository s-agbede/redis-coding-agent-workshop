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


@pytest.mark.parametrize("lab_id", ["zcqxlz", "tnvzfa"])
def test_hosted_lab_origin_survives_internal_proxy_address(
    tmp_path: Path, lab_id: str,
) -> None:
    sent: list[str] = []
    client = TestClient(create_app(tmp_path, run_terminal=sent.append), base_url=f"http://rl-s-labs-{lab_id}")
    response = client.post(
        "/api/terminal/run", json={"command": "pwd"},
        headers={
            "Origin": f"https://8080-p-rl-s-labs-{lab_id}.labs.ps-redis.com",
            "Sec-Fetch-Site": "same-origin",
            "X-Forwarded-Proto": "http",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    assert sent == ["pwd"]


@pytest.mark.parametrize("fetch_site", [None, "", "same-site", "cross-site", "none"])
def test_hosted_lab_fallback_requires_explicit_same_origin_metadata(
    terminal_client: tuple[TestClient, list[str]], fetch_site: str | None,
) -> None:
    client, sent = terminal_client
    headers = {"Origin": "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com"}
    if fetch_site is not None:
        headers["Sec-Fetch-Site"] = fetch_site
    response = client.post("/api/terminal/run", json={"command": "pwd"}, headers=headers)
    assert response.status_code == 403
    assert response.json()["diagnostics"]["sec_fetch_site"] == fetch_site
    assert not sent


@pytest.mark.parametrize("origin", [
    "http://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com:8443",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com/",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com?x=1",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com#fragment",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com.evil.test",
    "https://8080-p-rl-s-labs-zcqxlz.labs.fakeps-redis.com",
    "https://user@8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com",
    "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com@evil.test",
    "https://8080-p-rl-s-labs-.labs.ps-redis.com",
    "https://8080-p-rl-s-labs-zcqxlz.extra.labs.ps-redis.com",
    "https://8081-p-rl-s-labs-zcqxlz.labs.ps-redis.com",
    "https://other.labs.ps-redis.com",
    "https://ps-redis.com",
    "null",
    "https://evil.test",
    "https://8080-p-rl-s-labs-" + "a" * 47 + ".labs.ps-redis.com",
])
def test_hosted_lab_fallback_rejects_other_or_malformed_origins(
    terminal_client: tuple[TestClient, list[str]], origin: str,
) -> None:
    client, sent = terminal_client
    response = client.post(
        "/api/terminal/run", json={"command": "pwd"},
        headers={"Origin": origin, "Sec-Fetch-Site": "same-origin"},
    )
    assert response.status_code == 403
    assert not sent


def test_hosted_lab_still_requires_json(terminal_client: tuple[TestClient, list[str]]) -> None:
    client, sent = terminal_client
    response = client.post(
        "/api/terminal/run", content='{"command":"pwd"}',
        headers={
            "Origin": "https://8080-p-rl-s-labs-zcqxlz.labs.ps-redis.com",
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "text/plain",
        },
    )
    assert response.status_code == 415
    assert not sent


def test_preview_status_reports_only_ready_selection(tmp_path: Path, monkeypatch) -> None:
    selection = tmp_path / "preview"
    monkeypatch.setenv("WORKSHOP_PREVIEW_FILE", str(selection))
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/preview").status_code == 503
    selection.with_suffix(".ready").write_text(json.dumps({"mode": "demo", "revision": "demo-copy"}))
    assert client.get("/api/preview").json() == {"mode": "demo", "revision": "demo-copy"}
