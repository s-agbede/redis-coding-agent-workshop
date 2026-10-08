"""Check published lesson references and mirrored content, not teaching prose."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = (
    "01-first-call.md",
    "02-peas.md",
    "03-conversation.md",
    "04-one-tool.md",
    "05-better-tools.md",
    "06-agent-loop.md",
    "07-capstone.md",
)


def without_frontmatter(text: str) -> str:
    body = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL).strip()
    return re.sub(r"\A# [^\n]+\n+", "", body).strip()


def test_active_lessons_exist_and_have_revealable_answers() -> None:
    for name in LESSONS:
        lesson = ROOT / "docs/tasks" / name
        text = lesson.read_text()
        assert "<details>" in text, lesson
        assert text.count("<details>") == text.count("</details>"), lesson
        assert text.count("<summary>") == text.count("</summary>"), lesson


def test_workshop_markdown_links_resolve() -> None:
    missing: list[str] = []
    for path in (ROOT / "docs").rglob("*.md"):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)", path.read_text()):
            if link.startswith(("http://", "https://", "/")):
                continue
            if not (path.parent / link).resolve().is_file():
                missing.append(f"{path.relative_to(ROOT)}: {link}")
    assert not missing, "\n".join(missing)


def test_lesson_python_and_test_commands_reference_real_files() -> None:
    for name in LESSONS:
        text = (ROOT / "docs/tasks" / name).read_text()
        for command in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
            for module in re.findall(r"uv run python -m ([\w.]+)", command):
                assert (ROOT / (module.replace(".", "/") + ".py")).is_file(), (name, module)
            for file in re.findall(r"uv run (?:python|pytest) ([\w/]+\.py)", command):
                assert (ROOT / file).is_file(), (name, file)


def test_sidebar_links_to_every_active_lesson() -> None:
    sidebar = (ROOT / "docs/_sidebar.md").read_text()
    for name in LESSONS:
        assert f"#/tasks/{Path(name).stem})" in sidebar


def test_docs_include_vscode_panel_bridge() -> None:
    index = (ROOT / "docs/index.html").read_text()
    assert "open-vscode-file" in index
    assert 'a[target="vscode"][href^="/vscode/"]' in index
    assert "open-docs-route" in index


def test_published_lesson_manifest_and_mirrors() -> None:
    # The student distribution has no frontend sibling inside its workspace.
    public = ROOT / "docker-workshop/frontend/public/build-steps"
    if not public.is_dir():
        return
    manifest = (public / "manifest.yaml").read_text()
    assert tuple(re.findall(r"^\s+- file: (\S+)$", manifest, re.MULTILINE)) == LESSONS
    mirrors = (ROOT / "docker-workshop/student/docs/tasks", ROOT / "docker-workshop/docs/tasks", public)
    for name in LESSONS:
        expected = without_frontmatter((ROOT / "docs/tasks" / name).read_text())
        for mirror in mirrors:
            actual = without_frontmatter((mirror / name).read_text())
            # Assets are rooted at /images in the guided frontend.
            actual = actual.replace("](/images/", "](../images/")
            assert actual == expected, mirror / name
        for editor_file in re.findall(r"^editorFile: (.+)$", (public / name).read_text(), re.MULTILINE):
            assert (ROOT / editor_file).is_file(), (name, editor_file)
