import json
from pathlib import Path
from typing import BinaryIO

import pytest
from fastapi.testclient import TestClient

import app as editor
from app import create_app


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "agent.py").write_text("print('hello')\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_agent.py").write_text("assert True\n", encoding="utf-8")
    return root


@pytest.fixture
def client(workspace: Path) -> TestClient:
    return TestClient(create_app(workspace))


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lists_editable_files_recursively(client: TestClient, workspace: Path) -> None:
    (workspace / "README.md").write_text("# Workshop\n", encoding="utf-8")
    for directory in (".venv", "node_modules", "__pycache__", ".git", ".pytest_cache", ".hidden"):
        (workspace / directory).mkdir()
        (workspace / directory / "secret.py").write_text("hidden", encoding="utf-8")
    (workspace / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (workspace / ".secret.py").write_text("secret", encoding="utf-8")
    (workspace / "picture.png").write_bytes(b"image")
    (workspace / "binary.py").write_bytes(b"\xff\x00")
    (workspace / "linked.py").symlink_to(workspace / "agent.py")
    (workspace / "linked-tests").symlink_to(workspace / "tests", target_is_directory=True)

    response = client.get("/api/editor/files")

    assert response.status_code == 200
    assert response.json() == [
        {"name": "README.md", "path": "README.md", "language": "markdown"},
        {"name": "agent.py", "path": "agent.py", "language": "python"},
        {"name": "test_agent.py", "path": "tests/test_agent.py", "language": "python"},
    ]


@pytest.mark.parametrize(
    ("suffix", "language"),
    [
        ("py", "python"), ("toml", "toml"), ("md", "markdown"),
        ("txt", "plaintext"), ("json", "json"), ("yaml", "yaml"),
        ("yml", "yaml"), ("sh", "shell"), ("html", "html"),
        ("css", "css"), ("js", "javascript"), ("ts", "typescript"),
    ],
)
def test_reads_supported_text_types(
    client: TestClient, workspace: Path, suffix: str, language: str
) -> None:
    path = f"example.{suffix}"
    (workspace / path).write_text("sample\n", encoding="utf-8")

    response = client.get("/api/editor/file", params={"path": path})

    assert response.status_code == 200
    assert response.json() == {"path": path, "content": "sample\n", "language": language}


def test_saves_nested_file_and_reads_persisted_unicode(
    client: TestClient, workspace: Path
) -> None:
    path = "tests/test_agent.py"
    content = "# A café test 🐍\nassert 2 + 2 == 4\n"

    response = client.post("/api/editor/file", json={"path": path, "content": content})

    assert response.status_code == 200
    assert response.json() == {"path": path, "content": content, "language": "python"}
    assert (workspace / path).read_text(encoding="utf-8") == content
    assert client.get("/api/editor/file", params={"path": path}).json() == response.json()


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize(
    "path", ["../outside.py", "../workspace-other/outside.py", ".env", ".secret.py",
             ".venv/source.py", "node_modules/source.py", "__pycache__/source.py",
             "tests/../../outside.py", "tests/../agent.py", "picture.png"]
)
def test_rejects_disallowed_paths_without_modifying_files(
    client: TestClient, workspace: Path, method: str, path: str
) -> None:
    outside = workspace.parent / "outside.py"
    outside.write_text("keep", encoding="utf-8")
    sibling = workspace.parent / "workspace-other"
    sibling.mkdir()
    (sibling / "outside.py").write_text("keep", encoding="utf-8")
    for blocked in (".env", ".secret.py", ".venv/source.py", "node_modules/source.py",
                    "__pycache__/source.py", "picture.png"):
        target = workspace / blocked
        target.parent.mkdir(exist_ok=True)
        target.write_text("keep", encoding="utf-8")

    if method == "get":
        response = client.get("/api/editor/file", params={"path": path})
    else:
        response = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert response.status_code == 403
    assert response.json()["detail"]
    assert outside.read_text(encoding="utf-8") == "keep"
    assert (sibling / "outside.py").read_text(encoding="utf-8") == "keep"
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"
    for blocked in (".env", ".secret.py", ".venv/source.py", "node_modules/source.py",
                    "__pycache__/source.py", "picture.png"):
        assert (workspace / blocked).read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("method", ["get", "post"])
def test_rejects_absolute_paths_even_inside_workspace(
    client: TestClient, workspace: Path, method: str
) -> None:
    path = str(workspace / "agent.py")

    if method == "get":
        response = client.get("/api/editor/file", params={"path": path})
    else:
        response = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert response.status_code == 403
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"


@pytest.mark.parametrize("link_kind", ["internal-file", "external-file", "ancestor"])
def test_rejects_symlinks_for_reads_and_writes(
    client: TestClient, workspace: Path, link_kind: str
) -> None:
    outside = workspace.parent / "outside"
    outside.mkdir()
    target = outside / "secret.py"
    target.write_text("keep", encoding="utf-8")
    if link_kind == "internal-file":
        path = "link.py"
        (workspace / path).symlink_to(workspace / "agent.py")
    elif link_kind == "external-file":
        path = "link.py"
        (workspace / path).symlink_to(target)
    else:
        path = "linked/secret.py"
        (workspace / "linked").symlink_to(outside, target_is_directory=True)

    read = client.get("/api/editor/file", params={"path": path})
    write = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert read.status_code == 403
    assert write.status_code == 403
    assert target.read_text(encoding="utf-8") == "keep"
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"


def test_missing_file_returns_clear_404_without_creating_file(
    client: TestClient, workspace: Path
) -> None:
    read = client.get("/api/editor/file", params={"path": "missing.py"})
    write = client.post("/api/editor/file", json={"path": "missing.py", "content": "new"})

    assert read.status_code == 404
    assert write.status_code == 404
    assert "file" in read.json()["detail"].lower()
    assert "file" in write.json()["detail"].lower()
    assert not (workspace / "missing.py").exists()


@pytest.mark.parametrize(
    "content", [1, None, [], {}, "a" * (1024 * 1024 + 1), "🐍" * 300_000],
    ids=["integer", "null", "list", "object", "too-many-characters", "too-many-bytes"],
)
def test_rejects_invalid_content_without_overwriting(
    client: TestClient, workspace: Path, content: object
) -> None:
    response = client.post("/api/editor/file", json={"path": "agent.py", "content": content})

    assert response.status_code == 422
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"


@pytest.mark.parametrize("body", [{}, {"path": "agent.py"}, {"content": "new"},
                                  {"path": 1, "content": "new"}, {"path": "", "content": "new"}])
def test_rejects_missing_or_invalid_request_fields(client: TestClient, body: object) -> None:
    assert client.post("/api/editor/file", json=body).status_code == 422


def test_rejects_binary_file(client: TestClient, workspace: Path) -> None:
    (workspace / "binary.py").write_bytes(b"\xff\x00")

    response = client.get("/api/editor/file", params={"path": "binary.py"})

    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_uses_workspace_environment_variable(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WORKSPACE_ROOT", str(workspace))
    client = TestClient(create_app())

    response = client.get("/api/editor/file", params={"path": "agent.py"})

    assert response.status_code == 200
    assert response.json()["content"] == "print('hello')\n"


@pytest.mark.parametrize("method", ["get", "post"])
def test_rejects_path_components_too_long_for_the_filesystem(
    workspace: Path, method: str
) -> None:
    client = TestClient(create_app(workspace), raise_server_exceptions=False)
    path = "x" * 300 + ".py"

    if method == "get":
        response = client.get("/api/editor/file", params={"path": path})
    else:
        response = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file path."
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"


@pytest.mark.parametrize(
    ("field", "invalid_text"),
    [("path", "\ud800.py"), ("content", "\ud800"),
     ("path", "\udfff" * 4097), ("content", "\ud800" * (1024 * 1024 + 1))],
    ids=["path", "content", "oversized-path", "oversized-content"],
)
def test_rejects_json_lone_surrogates_without_overwriting(
    workspace: Path, field: str, invalid_text: str
) -> None:
    client = TestClient(create_app(workspace), raise_server_exceptions=False)
    body = {"path": "agent.py", "content": "changed", field: invalid_text}

    response = client.post(
        "/api/editor/file", content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", field] and error["type"] == "string_unicode"
        for error in response.json()["detail"]
    )
    assert (workspace / "agent.py").read_text(encoding="utf-8") == "print('hello')\n"


@pytest.mark.parametrize("directory", ["dist", "build"])
def test_excludes_build_outputs_from_listing_reads_and_writes(
    client: TestClient, workspace: Path, directory: str
) -> None:
    (workspace / directory).mkdir()
    path = f"{directory}/output.js"
    generated = workspace / path
    generated.write_text("keep", encoding="utf-8")

    listed = client.get("/api/editor/files")
    read = client.get("/api/editor/file", params={"path": path})
    write = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert listed.status_code == 200
    assert path not in [file["path"] for file in listed.json()]
    assert read.status_code == 403
    assert write.status_code == 403
    assert generated.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("replacement", ["file", "ancestor"])
def test_rejects_symlink_inserted_after_path_validation(
    client: TestClient, workspace: Path, monkeypatch: pytest.MonkeyPatch,
    method: str, replacement: str,
) -> None:
    outside = workspace.parent / "outside"
    outside.mkdir()
    secret = outside / "test_agent.py"
    secret.write_text("outside-secret", encoding="utf-8")
    original_check = editor.checked_file

    def swap_after_check(root: Path, path: str) -> Path:
        checked = original_check(root, path)
        if replacement == "file":
            checked.unlink()
            checked.symlink_to(secret)
        else:
            (workspace / "tests").rename(workspace / "original-tests")
            (workspace / "tests").symlink_to(outside, target_is_directory=True)
        return checked

    monkeypatch.setattr(editor, "checked_file", swap_after_check)
    path = "tests/test_agent.py"

    if method == "get":
        response = client.get("/api/editor/file", params={"path": path})
    else:
        response = client.post("/api/editor/file", json={"path": path, "content": "changed"})

    assert response.status_code == 403
    assert "outside-secret" not in response.text
    assert secret.read_text(encoding="utf-8") == "outside-secret"


def test_save_keeps_the_same_file_open_after_checking_its_content(
    client: TestClient, workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = workspace.parent / "secret.py"
    secret.write_text("outside-secret", encoding="utf-8")
    original_read = editor.read_content

    def replace_after_read(stream: BinaryIO) -> str:
        content = original_read(stream)
        (workspace / "agent.py").rename(workspace / "original-agent.py")
        (workspace / "agent.py").symlink_to(secret)
        return content

    monkeypatch.setattr(editor, "read_content", replace_after_read)

    response = client.post(
        "/api/editor/file", json={"path": "agent.py", "content": "changed"}
    )

    assert response.status_code == 200
    assert (workspace / "original-agent.py").read_text(encoding="utf-8") == "changed"
    assert secret.read_text(encoding="utf-8") == "outside-secret"
