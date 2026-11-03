import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import { renderMarkdown } from '../../vendor/workshop-front-end-components/src/content-renderer/markdown.js'

test('hint disclosures start closed and preserve Python code', () => {
  const html = renderMarkdown('Try first.\n\n<details>\n<summary>Hint 1</summary>\n\n```python\nreturn reader(**args)\n```\n\n</details>')
  assert.ok(html.includes('<details><summary>Hint 1</summary>'))
  assert.ok(!html.includes('<details open'))
  assert.ok(html.includes('return reader(**args)'))
  assert.ok(html.endsWith('</details>'))
})

test('disclosures do not enable arbitrary HTML or summary event handlers', () => {
  const html = renderMarkdown('<details>\n<summary><img src=x onerror=alert(1)></summary>\n\n<script>alert(1)</script>\n</details>')
  assert.ok(!html.includes('<img'))
  assert.ok(!html.includes('<script>'))
  assert.ok(html.includes('&lt;script&gt;'))
})

test('Python code survives Markdown rendering without losing indentation or **kwargs', () => {
  const code = 'try:\n    result = registry[name](**args)\nexcept Exception as exc:\n    result = f"Error: {exc}"'
  const html = renderMarkdown('```python\n' + code + '\n```')
  assert.ok(html.includes('    result = registry[name](**args)'))
  assert.ok(!html.includes('<em>'))
  assert.ok(!html.includes('<br>'))
})

test('the six memory lessons follow the agreed learning order and link to existing exercise files', async () => {
  const manifest = await readFile(new URL('../public/build-steps/manifest.yaml', import.meta.url), 'utf8')
  const names = [...manifest.matchAll(/- file: (.+)/g)].map(match => match[1])
  assert.deepEqual(names, ['01-recap.md', '02-forgetting.md', '03-capture.md', '04-recall.md', '05-playbook.md'])
  for (const name of names) {
    const lesson = await readFile(new URL('../public/build-steps/' + name, import.meta.url), 'utf8')
    assert.ok(!lesson.includes('/vscode/'))
    const path = lesson.match(/^editorFile: (.+)$/m)?.[1]
    assert.ok(!path.startsWith('part2/'))
    assert.ok(path, `${name} needs an editor file`)
    await readFile(new URL('../../../' + path, import.meta.url), 'utf8')
  }
})

test('tables render semantic headers and cells while retaining code pipes and escaping HTML', () => {
  const html = renderMarkdown('Before\n| Role | Example |\n| --- | :---: |\n| **Program** | `reader(**args)` |\n| Model | `a | b` |\n| Input | <script>bad()</script> |\n\nAfter')
  assert.match(html, /<p>Before<\/p>/)
  assert.match(html, /<th scope="col">Role<\/th>/)
  assert.match(html, /<td><code>reader\(\*\*args\)<\/code><\/td>/)
  assert.match(html, /<td><code>a \| b<\/code><\/td>/)
  assert.match(html, /&lt;script&gt;/)
  assert.doesNotMatch(html, /<script>/)
  assert.match(html, /<p>After<\/p>/)
})

test('local Markdown images have accessible escaped alt text and support a workshop proxy prefix', () => {
  const html = renderMarkdown('![Model & "program"](/images/agent-map.svg)', { assetBasePath: '/hub/workshop/agent' })
  assert.match(html, /<img src="\/hub\/workshop\/agent\/images\/agent-map.svg" alt="Model &amp; &quot;program&quot;"/)
  assert.doesNotMatch(html, /<svg/)
})

test('Markdown images reject remote, executable, traversal and injected paths', () => {
  for (const path of ['https://example.com/a.svg', '//example.com/a.svg', 'javascript:alert', 'data:image/svg+xml,x', '/images/../secret.svg', '/images/%2e%2e/secret.svg', '/images/x.svg"onerror="bad', '/other/map.svg']) {
    assert.doesNotMatch(renderMarkdown(`![Diagram](${path})`), /<img|<svg|<script/)
  }
  const html = renderMarkdown('![`<img src=x>`](/images/agent-map.svg)\n\n<svg onload="bad()"></svg>')
  assert.match(html, /alt="`&lt;img src=x&gt;`"/)
  assert.doesNotMatch(html, /<svg|<img src=x/)
})

test('page and lesson Markdown image URLs follow the current workshop proxy', async () => {
  globalThis.window = { location: { pathname: '/hub/workshop/agent/build' } }
  for (const path of ['../src/utils/buildSteps.js', '../src/utils/pageContent.js']) {
    const { markdownToHtml } = await import(path)
    assert.match(markdownToHtml('![Map](/images/agent-map.svg)'), /src="\/hub\/workshop\/agent\/images\/agent-map.svg"/)
  }
})

test('emphasis spans inline code without interpreting code as emphasis or HTML', () => {
  assert.equal(
    renderMarkdown('**only `run_bash` and `web_fetch` are gated**; *inspect `reader(**args)` first*'),
    '<p><strong>only <code>run_bash</code> and <code>web_fetch</code> are gated</strong>; <em>inspect <code>reader(**args)</code> first</em></p>'
  )
  assert.equal(renderMarkdown('**`<img src=x onerror=bad()>`**'), '<p><strong><code>&lt;img src=x onerror=bad()&gt;</code></strong></p>')
})

test('emphasis can wrap a safe image while its alt text remains escaped literal text', () => {
  assert.equal(
    renderMarkdown('**Map: ![**literal** "<svg>"](/images/agent-map.svg)**'),
    '<p><strong>Map: <img src="/images/agent-map.svg" alt="**literal** &quot;&lt;svg&gt;&quot;" loading="lazy"></strong></p>'
  )
})


test('welcome content defaults to 90 minutes when duration metadata is missing', async () => {
  const originalFetch = globalThis.fetch
  const originalWindow = globalThis.window
  globalThis.window = { location: { pathname: '/guide/' } }
  globalThis.fetch = async () => new Response('# Welcome')
  try {
    const { loadWelcomeContent } = await import('../src/utils/pageContent.js')
    assert.equal((await loadWelcomeContent()).estimatedMinutes, 90)
  } finally {
    globalThis.fetch = originalFetch
    globalThis.window = originalWindow
  }
})


test('the single workshop loads its root manifest, lessons and welcome', async () => {
  const oldFetch = globalThis.fetch
  const oldWindow = globalThis.window
  const requests = []
  globalThis.window = { location: { pathname: '/guide/build' } }
  globalThis.fetch = async url => {
    requests.push(url)
    if (url.endsWith('manifest.yaml')) return new Response('steps:\n  - file: 01-existing-agent.md\n    title: Existing agent\n')
    if (url.endsWith('welcome.md')) return new Response('---\ntitle: Memory workshop\n---\nWelcome')
    return new Response('---\ntitle: Existing agent\neditorFile: agent.py\n---\nInspect your agent.')
  }
  try {
    const { loadAllBuildSteps } = await import('../src/utils/buildSteps.js')
    const { loadWelcomeContent } = await import('../src/utils/pageContent.js')
    assert.equal((await loadAllBuildSteps())[0].editorFile, 'agent.py')
    assert.equal((await loadWelcomeContent()).title, 'Memory workshop')
    await loadWelcomeContent()
    assert.deepEqual(requests, ['/guide/build-steps/manifest.yaml', '/guide/build-steps/01-existing-agent.md', '/guide/welcome.md', '/guide/welcome.md'])
  } finally {
    globalThis.fetch = oldFetch
    globalThis.window = oldWindow
  }
})

test('Root local lesson and reference links stay within the guide proxy', async () => {
  globalThis.window = { location: { pathname: '/hub/workshop/agent/build' } }
  const { markdownToHtml } = await import('../src/utils/markdown.js')
  const html = markdownToHtml('[Next](/build?lesson=04-capture.md)\n[Contract](/challenge/CONTRACT.md)')
  assert.match(html, /href="\/hub\/workshop\/agent\/build\?lesson=04-capture.md"/)
  assert.match(html, /href="\/hub\/workshop\/agent\/challenge\/CONTRACT.md"/)
  assert.doesNotMatch(html, /target="_blank"/)
})


test('local reference links reject traversal, encoded paths and attribute injection', () => {
  for (const path of ['/challenge/../secret', '/challenge/%2e%2e/secret', '//evil.test/challenge', '/challenge/x"onclick="bad', '/build?lesson=../secret', '/other/path']) {
    assert.doesNotMatch(renderMarkdown(`[Reference](${path})`), /<a /)
  }
  assert.match(renderMarkdown('[Web](https://example.com)'), /target="_blank"/)
})

test('published skills and solution references remain clickable within the guide', () => {
  for (const path of ['/skills/report-validation/SKILL.md', '/solutions/validator.py']) {
    assert.ok(renderMarkdown(`[Reference](${path})`, { assetBasePath: '/guide' }).includes(`href="/guide${path}"`))
  }
  for (const path of ['/skills/../secret', '/solutions/%2e%2e/secret', '/skills/x"onclick="bad', '/solutions/./validator.py', '/skills//report.md']) {
    assert.doesNotMatch(renderMarkdown(`[Reference](${path})`), /<a /)
  }
})

test('frontend image supplies every lesson editor file before running content tests', async () => {
  const dockerfile = await readFile(new URL('../Dockerfile', import.meta.url), 'utf8')
  const beforeTests = dockerfile.split('RUN npm test')[0]
  assert.match(beforeTests, /COPY agent\.py \/workshop\/agent\.py/)
  assert.match(beforeTests, /COPY project \/workshop\/project/)
})
