"""Publish this branch's single memory workshop; never modify learner files."""
from __future__ import annotations
import argparse
import posixpath
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = (
    '01-recap.md', '02-forgetting.md', '03-capture.md',
    '04-recall.md', '05-playbook.md', '06-verify.md',
)
# Each lesson shows its section of the presenter deck: docs/slides/<lesson>.md holds the slide images,
# rendered from docs/deck by scripts/render_slides.py.
SLIDES = {lesson: lesson for lesson in LESSONS}


# Named places in agent.py that lessons link to as `agent.py:<name>`; each resolves to the first line
# containing its marker, so the links stay right when agent.py changes.
AGENT_ANCHORS = {
    'loop': 'def run_agent(',
    'flags': 'CAPTURE = ',
    'handle': 'def handle(',
    'capture': '# Section 3: record',
    'recall': '# Section 4: search',
    'playbook': '# Section 5: the team',
    'request': '# Build the request',
    'answer': '# Section 3 again',
}


def agent_line_links(text: str, agent_source: str) -> str:
    lines = agent_source.splitlines()
    def line_of(name: str) -> str:
        marker = AGENT_ANCHORS[name]
        return str(next(number for number, line in enumerate(lines, start=1) if marker in line))
    return re.sub(r'`agent\.py:([a-z]+)`', lambda match: f'`agent.py:{line_of(match[1])}`', text)


def lesson_links(text: str, source: str) -> str:
    def replace(match: re.Match[str]) -> str:
        url = match[1]
        if url.startswith(('/', '#')) or ':' in url:
            return match[0]
        path, separator, anchor = url.partition('#')
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
        if resolved.startswith('docs/tasks/') and posixpath.basename(resolved) in LESSONS:
            target = '/build?lesson=' + posixpath.basename(resolved)
        elif resolved.startswith('docs/images/'):
            target = '/' + resolved.removeprefix('docs/')
        elif resolved.startswith(('skills/', 'solutions/', 'project/', 'docs/')) or resolved in ('WORKSHOP.md', 'FACILITATOR.md'):
            target = '/' + resolved
        else:
            return match[0]
        return '](' + target + separator + anchor + ')'
    return re.sub(r'\]\(([^\s)]+)\)', replace, text)


def published_files(root: Path) -> dict[Path, bytes]:
    docs = root / 'docs'
    public = root / 'docker-workshop/frontend/public'
    outputs: dict[Path, bytes] = {}
    for folder in ('tasks', 'slides', 'images'):
        for source in sorted((docs / folder).rglob('*')):
            if source.is_file():
                relative = source.relative_to(docs)
                outputs[root / 'docker-workshop/docs' / relative] = source.read_bytes()
                if folder in ('slides', 'images'):
                    outputs[public / relative] = source.read_bytes()
    for name in ('home.md', 'welcome.md'):
        if (docs / name).exists():
            outputs[root / 'docker-workshop/docs' / name] = (docs / name).read_bytes()
    for name in ('WORKSHOP.md', 'FACILITATOR.md'):
        if (root / name).is_file():
            outputs[public / name] = lesson_links((root / name).read_text(), name).encode()
    for folder in ('skills', 'solutions', 'project'):
        for source in sorted((root / folder).rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts and source.suffix in ('.md', '.py', '.json'):
                outputs[public / source.relative_to(root)] = source.read_bytes()
    manifest = ['steps:']
    for name in LESSONS:
        heading, body = (docs / 'tasks' / name).read_text().split('\n', 1)
        if not heading.startswith('# '):
            raise ValueError(f'Lesson {name} must start with its title')
        title = heading.removeprefix('# ')
        editor = 'project/AGENTS.md' if name == '02-forgetting.md' else 'agent.py'
        deck = SLIDES.get(name)
        slide_metadata = f'slides: /slides/{deck}\n' if deck and (docs / 'slides' / deck).is_file() else ''
        frontmatter = f'---\ntitle: {title}\neditorFile: {editor}\n{slide_metadata}---\n'
        body = agent_line_links(body, (root / 'agent.py').read_text())
        outputs[public / 'build-steps' / name] = (frontmatter + lesson_links(body.lstrip('\n'), f'docs/tasks/{name}')).encode()
        manifest.extend((f'  - file: {name}', f'    title: {title}'))
    outputs[public / 'build-steps/manifest.yaml'] = ('\n'.join(manifest) + '\n').encode()
    # The guide's welcome hero reads its title and subtitle from front matter.
    hero = ('---\ntitle: Give a coding agent useful memory\n'
            'subtitle: Part 2 · Redis Agent Memory and Redis Agent Playbook\n---\n')
    outputs[public / 'welcome.md'] = (hero + lesson_links((docs / 'welcome.md').read_text(), 'docs/welcome.md')).encode()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = published_files(ROOT)
    changed = 0
    for directory in (ROOT / 'docker-workshop/docs', ROOT / 'docker-workshop/frontend/public/build-steps', ROOT / 'docker-workshop/frontend/public/slides'):
        for obsolete in sorted(directory.rglob('*.md')):
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
        print('Published documentation is up to date.')
    return int(args.check and changed > 0)


if __name__ == '__main__':
    raise SystemExit(main())
