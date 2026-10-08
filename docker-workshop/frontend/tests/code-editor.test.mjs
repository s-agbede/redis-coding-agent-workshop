import assert from 'node:assert/strict'
import { test } from 'node:test'
import { component, mount, findAll, textOf, flush } from './vue-harness.mjs'
import { EditorSession } from '../src/editorSession.ts'
import * as editorText from '../src/editorText.ts'

const CodeEditor = await component('../src/components/CodeEditor.vue', {
  '../editorSession': { EditorSession }, '../editorText': editorText,
  '../utils/basePath': { getApiUrl: path => path },
  'vue-router': { onBeforeRouteLeave() {} }
})
const response = data => ({ ok: true, json: async () => data })
function deferred() { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
function browser() { globalThis.window = { addEventListener() {}, removeEventListener() {} } }

test('a lesson request during the initial editor read opens the newest requested file', async () => {
  browser()
  const read = deferred()
  globalThis.fetch = async url => {
    if (url === '/api/editor/files') return response([{ path: 'first_call.py' }, { path: 'tools.py' }])
    const path = new URL(url, 'http://local').searchParams.get('path')
    if (path === 'first_call.py') return read.promise
    return response({ path, content: 'new lesson', language: 'python' })
  }
  const page = await mount(CodeEditor, { selectedFile: 'first_call.py' })
  page.vm.$.props.selectedFile = 'tools.py'
  await flush()
  read.resolve(response({ path: 'first_call.py', content: 'old lesson', language: 'python' }))
  await flush()
  assert.equal(findAll(page.root, el => el.type === 'textarea')[0].value, 'new lesson')
  assert.equal(findAll(page.root, el => el.type === 'select')[0].props.value, 'tools.py')
  page.unmount()
})

test('the textarea keeps selected code on Tab and keyboard undo restores it', async () => {
  browser()
  globalThis.fetch = async url => response(url === '/api/editor/files' ? [{ path: 'tools.py' }] : { path: 'tools.py', content: 'one()\ntwo()', language: 'python' })
  const page = await mount(CodeEditor, { selectedFile: 'tools.py' })
  const field = findAll(page.root, el => el.type === 'textarea')[0]
  field.setSelectionRange(0, field.value.length)
  field.props.onKeydown({ key: 'Tab', target: field, preventDefault() {} })
  await flush()
  assert.equal(field.value, '    one()\n    two()')
  field.props.onKeydown({ key: 'z', ctrlKey: true, target: field, preventDefault() {} })
  await flush()
  assert.equal(field.value, 'one()\ntwo()')
  assert.equal(field.selectionStart, 0)
  assert.equal(field.selectionEnd, field.value.length)
  page.unmount()
})

test('opening a file from a lesson focuses and reveals the editor, including the current file', async () => {
  browser()
  const reads = []
  const files = ['first_call.py', 'tools.py'].map(path => ({ path }))
  globalThis.fetch = async url => {
    if (url === '/api/editor/files') return response(files)
    const path = new URL(url, 'http://local').searchParams.get('path')
    reads.push(path)
    return response({ path, content: `# ${path}`, language: 'python' })
  }
  let available
  const page = await mount(CodeEditor, { onFilesLoaded: paths => { available = paths } })
  assert.deepEqual(available, ['first_call.py', 'tools.py'])
  assert.equal(typeof page.vm.openFile, 'function')
  await page.vm.openFile('tools.py', true)
  const field = findAll(page.root, el => el.type === 'textarea')[0]
  assert.equal(field.value, '# tools.py')
  assert.equal(field.focused, true)
  assert.equal(field.scrolledIntoView, true)
  field.focused = false
  await page.vm.openFile('tools.py', true)
  assert.equal(field.focused, true)
  assert.deepEqual(reads, ['first_call.py', 'tools.py'])
  page.unmount()
})

test('a failed save when opening a lesson file keeps the edited file visible', async () => {
  browser()
  const reads = []
  globalThis.fetch = async (url, init) => {
    if (url === '/api/editor/files') return response([{ path: 'first_call.py' }, { path: 'tools.py' }])
    if (init?.method === 'POST') return { ok: false, status: 503 }
    const path = new URL(url, 'http://local').searchParams.get('path')
    reads.push(path)
    return response({ path, content: '# original', language: 'python' })
  }
  const page = await mount(CodeEditor)
  const field = findAll(page.root, el => el.type === 'textarea')[0]
  field.value = '# my unsaved work'
  field.props.onInput({ target: field })
  assert.equal(typeof page.vm.openFile, 'function')
  await page.vm.openFile('tools.py', true)
  await flush()
  assert.equal(field.value, '# my unsaved work')
  assert.equal(findAll(page.root, el => el.type === 'select')[0].props.value, 'first_call.py')
  assert.deepEqual(reads, ['first_call.py'])
  assert.match(textOf(findAll(page.root, el => el.props.role === 'alert')[0]), /pending edits are kept/)
  page.unmount()
})
