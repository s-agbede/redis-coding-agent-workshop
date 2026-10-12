"""Publish canonical workshop docs without replacing learner code or app files.

Run from any directory. Use --check to report drift without changing files.
Historical research and design notes live in archive/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = (
    "01-first-call.md",
    "03-conversation.md",
    "06-agent-loop.md",
    "04-one-tool.md",
    "05-better-tools.md",
    "07-capstone.md",
)


def published_files(root: Path) -> dict[Path, bytes]:
    """Build the exact documentation outputs from their canonical sources."""
    docs = root / "docs"
    public = root / "docker-workshop/frontend/public"
    outputs: dict[Path, bytes] = {}
    for source in sorted(docs.rglob("*")):
        relative = source.relative_to(docs)
        if not source.is_file():
            continue
        outputs[root / "docker-workshop/docs" / relative] = source.read_bytes()
        if relative.parts[0] == "images":
            outputs[public / relative] = source.read_bytes()

    manifest = ["steps:"]
    for name in LESSONS:
        text = (docs / "tasks" / name).read_text(encoding="utf-8")
        heading, body = text.split("\n", 1)
        if not heading.startswith("# "):
            raise ValueError(f"Lesson {name} must start with its title")
        title = heading.removeprefix("# ")
        # The guided page supplies its own title; preserve its existing metadata.
        frontmatter = f"---\ntitle: {title}\neditorFile: agent.py\n---\n"
        body = body.lstrip("\n").replace("](../images/", "](/images/")
        outputs[public / "build-steps" / name] = (frontmatter + body).encode("utf-8")
        manifest.extend((f"  - file: {name}", f"    title: {title}"))
    outputs[public / "build-steps/manifest.yaml"] = ("\n".join(manifest) + "\n").encode("utf-8")
    outputs[public / "welcome.md"] = (docs / "welcome.md").read_bytes()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing files")
    args = parser.parse_args()
    changed = 0
    outputs = published_files(ROOT)
    for directory in (ROOT / "docker-workshop/docs", ROOT / "docker-workshop/frontend/public/build-steps"):
        for obsolete in sorted(directory.rglob("*.md")):
            if obsolete not in outputs:
                changed += 1
                print(f"{'Obsolete' if args.check else 'Removed'}: {obsolete.relative_to(ROOT)}")
                if not args.check:
                    obsolete.unlink()
    for destination, content in outputs.items():
        if destination.is_file() and destination.read_bytes() == content:
            continue
        changed += 1
        print(f"{'Out of date' if args.check else 'Published'}: {destination.relative_to(ROOT)}")
        if not args.check:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
    if not changed:
        print("Published documentation is up to date.")
    return int(args.check and changed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
