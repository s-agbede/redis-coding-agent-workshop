"""Render the presenter deck's slides to images for the browser guide.

    python3 scripts/render_slides.py [DECK_DIR]

DECK_DIR holds the Slides artifact's files (project/deck.json and project/slides/*.html);
the default is docs/deck. Each slide becomes docs/images/slides/NN-<id>.jpg at
1920x1080, rendered with headless Chrome, and each lesson's docs/slides/<lesson>.md lists the
slides of its section of the deck (the deck's sections, in order; the closing one joins the last). The whole deck is
also printed to docs/slides/agent-memory-workshop-slides.pdf, which the guide offers as a download. The Slides runtime's flow arrows (x-connector)
and check icons (x-icon) are drawn here as SVG so they survive outside the runtime.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
OUT = ROOT / 'docs/images/slides'
LESSONS = ROOT / 'docs/slides'
PDF = LESSONS / 'agent-memory-workshop-slides.pdf'

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400..700&family=JetBrains+Mono:wght@400;600&display=block">
<style>
  html, body {{ margin: 0; background: #0b1b24; }}
  section {{ width: 1920px; height: 1080px; box-sizing: border-box; position: relative; overflow: hidden; }}
  section * {{ margin: 0; box-sizing: border-box; }}
  section aside {{ display: none; }}
  section ul, section ol {{ padding-left: 1.3em; }}
  x-connector, x-icon {{ display: inline-block; flex: none; }}
  /* The Slides runtime rules its tables; match that outside it. */
  section table {{ border-collapse: collapse; width: 100%; }}
  section th, section td {{ text-align: left; vertical-align: top; padding: 0.35em 0.6em; border-bottom: 1px solid #dcd8cf; }}
  section th {{ border-bottom: 2px solid #0b1b24; }}
</style></head><body>{slide}
<script>
for (const c of document.querySelectorAll('x-connector')) {{
  const width = parseFloat(c.style.width) || 64, stroke = parseFloat(c.style.borderWidth) || 2, color = c.style.color || '#55636b';
  const height = Math.max(24, stroke * 8), y = height / 2, head = stroke * 4;
  c.innerHTML = `<svg width="${{width}}" height="${{height}}" viewBox="0 0 ${{width}} ${{height}}"><line x1="0" y1="${{y}}" x2="${{width - head}}" y2="${{y}}" stroke="${{color}}" stroke-width="${{stroke}}" stroke-linecap="round"/><path d="M${{width - head}} ${{y - head * 0.7}} L${{width}} ${{y}} L${{width - head}} ${{y + head * 0.7}} Z" fill="${{color}}"/></svg>`;
  c.style.height = height + 'px';
}}
for (const i of document.querySelectorAll('x-icon[name="Check"]')) {{
  const size = parseFloat(i.style.width) || 32, color = i.style.color || 'currentColor';
  i.innerHTML = `<svg width="${{size}}" height="${{size}}" viewBox="0 0 24 24" fill="none" stroke="${{color}}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 12.5 9.5 18 20 6.5"/></svg>`;
}}
</script></body></html>"""


def lesson_decks(deck: Path, order: list[str], sections: dict) -> None:
    """One slide list per lesson: lesson N shows deck section N; any extra sections join the last lesson."""
    lessons = sorted(path.name for path in (ROOT / 'docs/tasks').glob('*.md'))
    starts = [order.index(section['start']) for section in sections.values()] + [len(order)]
    groups = [order[start:end] for start, end in zip(starts, starts[1:])]
    groups = groups[:len(lessons) - 1] + [sum(groups[len(lessons) - 1:], [])]
    def title(slide_id: str) -> str:
        html = (deck / f'project/slides/{slide_id}.html').read_text()
        found = re.search(r'<h[12][^>]*>(.*?)</h[12]>', html, re.S)
        return re.sub(r'<[^>]+>', '', found.group(1)).replace('&amp;', '&').strip() if found else slide_id
    LESSONS.mkdir(exist_ok=True)
    for lesson, ids in zip(lessons, groups):
        slides = [f'![{title(i)}](/images/slides/{order.index(i) + 1:02d}-{i}.jpg)' for i in ids]
        (LESSONS / lesson).write_text('\n\n---\n\n'.join(slides) + '\n')


def deck_pdf(images: list[Path], work: Path) -> None:
    """Print the rendered slide images, one per 1920x1080 page, into a single PDF (speaker notes are not included)."""
    pages = ''.join(f'<img src="{image.as_uri()}">' for image in images)
    html = work / 'deck.html'
    html.write_text('<!doctype html><style>@page { size: 1920px 1080px; margin: 0 } body { margin: 0 }'
                    ' img { display: block; width: 1920px; height: 1080px; break-after: page }</style>' + pages)
    LESSONS.mkdir(exist_ok=True)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', f'--user-data-dir={work}/profile', '--no-pdf-header-footer',
                    '--allow-file-access-from-files', f'--print-to-pdf={PDF}', html.as_uri()], check=True, capture_output=True)
    print(PDF.relative_to(ROOT))


def main() -> None:
    deck = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'docs/deck'
    index = json.loads((deck / 'project/deck.json').read_text())
    order = index['order']
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('*.jpg'):
        old.unlink()
    images: list[Path] = []
    with tempfile.TemporaryDirectory() as work:
        for number, slide_id in enumerate(order, start=1):
            html = Path(work) / f'{slide_id}.html'
            html.write_text(PAGE.format(slide=(deck / f'project/slides/{slide_id}.html').read_text()))
            png = Path(work) / f'{slide_id}.png'
            subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                            f'--user-data-dir={work}/profile', '--window-size=1920,1080', '--virtual-time-budget=5000',
                            f'--screenshot={png}', html.as_uri()], check=True, capture_output=True)
            target = OUT / f'{number:02d}-{slide_id}.jpg'
            subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(png), '--out', str(target)],
                           check=True, capture_output=True)
            images.append(target)
            print(target.relative_to(ROOT))
        deck_pdf(images, Path(work))
    lesson_decks(deck, order, index['sections'])


if __name__ == '__main__':
    main()
