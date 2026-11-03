"""Resetting the workshop from the guide: same-origin only, and it reports where the backup went."""

from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app

ORIGIN = {"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"}


def client_with(resets: list[str], tmp_path: Path) -> TestClient:
    def reset() -> Path:
        resets.append("reset")
        return tmp_path / ".backups/reset-20261103-120000"
    return TestClient(create_app(tmp_path, run_terminal=lambda _command: None, reset_workspace=reset))


def test_reset_runs_and_names_the_backup(tmp_path: Path) -> None:
    resets: list[str] = []
    response = client_with(resets, tmp_path).post("/api/workspace/reset", json={}, headers=ORIGIN)
    assert response.status_code == 200
    assert response.json() == {"status": "reset", "backup": ".backups/reset-20261103-120000"}
    assert resets == ["reset"]


def test_reset_from_another_site_is_refused(tmp_path: Path) -> None:
    resets: list[str] = []
    response = client_with(resets, tmp_path).post(
        "/api/workspace/reset", json={}, headers={"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 403
    assert resets == []


def test_reset_requires_json(tmp_path: Path) -> None:
    resets: list[str] = []
    response = client_with(resets, tmp_path).post(
        "/api/workspace/reset", content="x", headers={**ORIGIN, "Content-Type": "text/plain"})
    assert response.status_code == 415
    assert resets == []
