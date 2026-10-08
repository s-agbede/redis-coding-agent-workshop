import assert from 'node:assert/strict'
import { test } from 'node:test'
import * as lessonContent from '../src/lessonContent.ts'
const { withCopyButtons, copyCode } = lessonContent
import { renderMarkdown } from '../../vendor/workshop-front-end-components/src/content-renderer/markdown.js'

test('shell blocks run in Terminal while source answers retain copy actions', () => {
  const html = renderMarkdown('```sh\nuv run first_call.py\n```\n\n<details>\n<summary>Hint</summary>\n\n```python\n    reader(**args)\n```\n\n</details>')
  const enhanced = withCopyButtons(html)
  assert.equal((enhanced.match(/data-run-code/g) || []).length, 1)
  assert.equal((enhanced.match(/data-copy-code/g) || []).length, 1)
  assert.match(enhanced, /Run code/)
  assert.match(enhanced, /<details><summary>Hint<\/summary>/)
  assert.match(enhanced, /    reader\(\*\*args\)/)
})

test('only shell languages get execution actions; prompts and protocol examples are copyable', () => {
  for (const language of ['bash', 'sh', 'shell']) {
    assert.match(withCopyButtons(renderMarkdown('```' + language + '\nprintf hello\n```')), /data-run-code/)
  }
  for (const language of ['python', 'json', 'text', '']) {
    const html = withCopyButtons(renderMarkdown('```' + language + '\nexample\n```'))
    assert.doesNotMatch(html, /data-run-code/)
    assert.match(html, /data-copy-code/)
  }
})

test('running sends the exact displayed command once and reports dispatch, not success', async () => {
  assert.equal(typeof lessonContent.runCode, 'function')
  const calls = []
  const command = 'uv run python first_call.py\nprintf "done\\n"'
  const result = await lessonContent.runCode(command, '/api/terminal/run', async (...args) => {
    calls.push(args)
    return new Response(JSON.stringify({ status: 'sent' }), { status: 200 })
  })
  assert.equal(calls.length, 1)
  assert.equal(calls[0][0], '/api/terminal/run')
  assert.equal(calls[0][1].method, 'POST')
  assert.equal(calls[0][1].headers['Content-Type'], 'application/json')
  assert.equal(calls[0][1].credentials, 'same-origin')
  assert.deepEqual(JSON.parse(calls[0][1].body), { command })
  assert.equal(result.ok, true)
  assert.match(result.message, /sent to terminal/i)
  assert.doesNotMatch(result.message, /passed|completed|succeeded/i)
})

test('busy terminals explain how to recover and uncertain requests are never retried', async () => {
  assert.equal(typeof lessonContent.runCode, 'function')
  const busy = await lessonContent.runCode('uv run python main.py', '/api/terminal/run', async () =>
    new Response(JSON.stringify({ detail: 'Terminal is busy. Exit the program, then try again.' }), { status: 409 }))
  assert.equal(busy.ok, false)
  assert.match(busy.message, /Terminal is busy/)
  let count = 0
  const uncertain = await lessonContent.runCode('uv run python main.py', '/api/terminal/run', async () => {
    count++
    throw new Error('connection lost')
  })
  assert.equal(count, 1)
  assert.equal(uncertain.ok, false)
  assert.match(uncertain.message, /check terminal before/i)
})

test('a non-JSON proxy error or unrecognized success is not reported as sent', async () => {
  assert.equal(typeof lessonContent.runCode, 'function')
  for (const response of [new Response('<html>Unavailable</html>', { status: 502 }), new Response('{}')]) {
    const result = await lessonContent.runCode('pwd', '/api/terminal/run', async () => response)
    assert.equal(result.ok, false)
  }
})

test('copy uses the exact code text and reports success', async () => {
  const text = '    result = reader(**args)\n    return "<ok>"'
  let copied
  const result = await copyCode(text, { writeText: async value => { copied = value } })
  assert.equal(copied, text)
  assert.deepEqual(result, { ok: true, message: 'Copied' })
})

test('clipboard denial or absence has an actionable visible error', async () => {
  for (const clipboard of [undefined, { writeText: async () => { throw new Error('denied') } }]) {
    const result = await copyCode('print(1)', clipboard)
    assert.equal(result.ok, false)
    assert.match(result.message, /select the code and copy/i)
  }
})

test('inline code and bold file references open only files available in the workspace', () => {
  const html = renderMarkdown('Open **first_call.py**. Inspect `checkpoints/history.py`, `missing.py` and `read_file`.\n\n| Source |\n| --- |\n| **`tools.py`** |')
  assert.equal(typeof lessonContent.withFileButtons, 'function')
  const result = lessonContent.withFileButtons(html, ['first_call.py', 'checkpoints/history.py', 'tools.py'])
  for (const path of ['first_call.py', 'checkpoints/history.py', 'tools.py']) {
    assert.ok(result.includes(`data-open-file="${path}"`))
    assert.ok(result.includes(`aria-label="Open ${path} in editor"`))
  }
  assert.equal((result.match(/data-open-file=/g) || []).length, 3)
  assert.match(result, /<code>missing.py<\/code>/)
})

test('file actions preserve code blocks and existing links without introducing unsafe paths', () => {
  assert.equal(typeof lessonContent.withFileButtons, 'function')
  const html = renderMarkdown('```text\nfirst_call.py\n```\n\n[**first_call.py**](https://example.com)\n\n`../secret.py` and `<img src=x>`')
  assert.equal(lessonContent.withFileButtons(html, ['first_call.py', '../secret.py', '<img src=x>']), html)
  assert.equal(lessonContent.withFileButtons('<strong>first_call.py</strong>', []), '<strong>first_call.py</strong>')
})
