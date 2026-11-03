"""Validate runnable instructions and the published single-workshop lesson set."""
import ast
import re
from pathlib import Path
from scripts.publish_docs import LESSONS, published_files

ROOT=Path(__file__).resolve().parents[1]


def test_active_lessons_and_revealable_answers():
    for name in LESSONS:
        text=(ROOT/'docs/tasks'/name).read_text()
        assert text.startswith('# ')
        assert text.count('<details>') == text.count('</details>')
        assert text.count('<summary>') == text.count('</summary>')
        assert 'part2/' not in text


def test_workshop_links_resolve():
    files=list((ROOT/'docs/tasks').glob('*.md'))+[ROOT/'docs/welcome.md',ROOT/'docs/home.md',ROOT/'WORKSHOP.md',ROOT/'FACILITATOR.md']
    missing=[]
    for path in files:
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',path.read_text()):
            if link.startswith(('http:', 'https:', '/', '#')):continue
            if not (path.parent/link.split('#')[0]).resolve().exists():missing.append((path.name,link))
    assert not missing


def test_code_examples_and_local_commands_are_valid():
    for name in LESSONS:
        text=(ROOT/'docs/tasks'/name).read_text()
        for code in re.findall(r'```python\n(.*?)```',text,re.S):ast.parse(code)
        for code in re.findall(r'```bash\n(.*?)```',text,re.S):
            for file in re.findall(r'uv run (?:--group iris )?(?:python|pytest) ([\w/]+\.py)',code):
                assert (ROOT/file).is_file(),(name,file)


def test_published_outputs_match_canonical_sources():
    if not (ROOT/'docker-workshop/frontend/public').exists():return
    for path,content in published_files(ROOT).items():
        assert path.is_file() and path.read_bytes()==content,str(path)


def test_lessons_carry_no_unfinished_placeholders():
    for name in LESSONS:
        assert 'placeholder' not in (ROOT/'docs/tasks'/name).read_text().lower(), name


def test_every_lesson_has_slides_whose_images_exist():
    for name in LESSONS:
        deck = (ROOT/'docs/slides'/name).read_text()
        images = re.findall(r'!\[[^\]]+\]\((/images/[^)]+)\)', deck)
        assert images, name
        for image in images:
            assert (ROOT/'docs'/image.lstrip('/')).is_file(), (name, image)


def test_lesson_links_into_agent_py_name_real_places():
    from scripts.publish_docs import AGENT_ANCHORS
    for name in LESSONS:
        for anchor in re.findall(r'`agent\.py:([a-z]+)`', (ROOT/'docs/tasks'/name).read_text()):
            assert anchor in AGENT_ANCHORS, (name, anchor)
