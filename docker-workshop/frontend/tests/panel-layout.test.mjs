import assert from 'node:assert/strict'
import { test } from 'node:test'
import { component, mount, findAll, flush, Stub } from './vue-harness.mjs'
import { EditorSession } from '../src/editorSession.ts'
import * as editorText from '../src/editorText.ts'
import { SelfChecks } from '../src/selfChecks.ts'

const PanelToggle = await component('../src/components/PanelToggle.vue')
const PanelDivider = await component('../src/components/PanelDivider.vue')
const CodeEditor = await component('../src/components/CodeEditor.vue', {
  '../editorSession': { EditorSession }, '../editorText': editorText,
  '../utils/basePath': { getApiUrl: path => path },
  'vue-router': { onBeforeRouteLeave() {} }
})
const AppEmbed = await component('../src/components/AppEmbed.vue', { '../utils/basePath': { getApiUrl: path => path } })
const BuildPanel = await component('../src/components/BuildPanel.vue', {
  './CodeEditor.vue': CodeEditor, './AppEmbed.vue': AppEmbed,
  './PanelToggle.vue': PanelToggle, './PanelDivider.vue': PanelDivider,
  '../utils/basePath': { getApiUrl: path => path }
})
const Build = await component('../src/views/Build.vue', {
  '@redis-workshop/components/components/WorkshopHeader.vue': Stub,
  '../components/BuildPanel.vue': BuildPanel,
  '../components/LessonContent.vue': Stub,
  '../components/PanelToggle.vue': PanelToggle,
  '../components/PanelDivider.vue': PanelDivider,
  '../utils/demoSteps': { loadAllDemoSteps: async () => [] },
  '../utils/buildSteps': { loadAllBuildSteps: async () => [], markdownToHtml: () => '' },
  '../utils/workshopConfig': {
    loadWorkshopConfig: async () => ({}), getPhaseStepTitles: () => [],
    getEnabledPhases: () => [], isPhaseEnabled: () => true
  },
  '../selfChecks': { SelfChecks }, '../utils/basePath': { getBasePath: () => '' }
})

function browser() {
  const events = new Map()
  globalThis.window = { innerWidth: 1400, localStorage: { getItem: () => null }, addEventListener() {}, removeEventListener() {} }
  globalThis.sessionStorage = { getItem: () => null, setItem() {} }
  globalThis.document = { addEventListener: (name, callback) => events.set(name, callback), removeEventListener: name => events.delete(name) }
  globalThis.fetch = async url => ({ ok: true, json: async () => url === '/api/editor/files' ? [{ path: 'first_call.py' }] : { path: 'first_call.py', content: 'original code', language: 'python' } })
  return events
}
function button(root, label) {
  const result = findAll(root, el => el.type === 'button' && (el.props['aria-label'] === label || el.text === label))[0]
  assert.ok(result, `Missing button: ${label}`)
  return result
}
async function click(root, label) { button(root, label).props.onClick(); await flush() }

for (const phase of ['build', 'demo']) {
  test(`${phase}: expanding all panels preserves unsaved code, frames and split sizes`, async () => {
    const events = browser()
    const page = await mount(Build, { phase })
    const field = findAll(page.root, el => el.type === 'textarea' && el.props.class === 'code-textarea')[0]
    field.props.onInput({ target: { value: 'unsaved code', selectionStart: 3, selectionEnd: 3 } })
    await flush()
    const terminal = findAll(page.root, el => el.type === 'iframe')[0]
    const editorDivider = findAll(page.root, el => el.props['aria-label'] === 'Resize editor and runtime')[0]
    assert.ok(editorDivider, 'Editor/runtime split must be resizable')
    editorDivider.props.onKeydown({ key: 'ArrowUp', preventDefault() {} })
    await flush()
    const split = editorDivider.props['aria-valuenow']
    await click(page.root, 'Expand code editor')
    assert.equal(button(page.root, 'Restore code editor').props['aria-pressed'], true)
    assert.equal(findAll(page.root, el => el.props.class === 'build-instructions')[0].props.hidden, true)
    events.get('keydown')({ key: 'Escape' })
    await flush()
    button(page.root, 'Expand code editor')
    await click(page.root, 'Expand terminal')
    await click(page.root, 'App Preview')
    button(page.root, 'Restore app preview')
    const preview = findAll(page.root, el => el.type === 'iframe' && el !== terminal)[0]
    await click(page.root, 'Restore app preview')
    await click(page.root, 'Expand instructions')
    assert.equal(findAll(page.root, el => el.props.class === 'build-interactive-panel')[0].props.hidden, true)
    await click(page.root, 'Restore instructions')
    assert.equal(findAll(page.root, el => el.type === 'textarea' && el.props.class === 'code-textarea')[0], field)
    assert.equal(field.value, 'unsaved code')
    assert.deepEqual(findAll(page.root, el => el.type === 'iframe'), [terminal, preview])
    assert.equal(editorDivider.props['aria-valuenow'], split)
    page.unmount()
    assert.equal(events.has('keydown'), false)
  })
}

test('dividers resize by keyboard and pointer, clamp sizes and stop on cancellation', async () => {
  const values = []
  const page = await mount(PanelDivider, { orientation: 'horizontal', label: 'Resize panels', value: 55, 'onUpdate:value': value => values.push(value) })
  const divider = findAll(page.root, el => el.props.role === 'separator')[0]
  assert.ok(divider, 'A focusable separator must be rendered')
  assert.equal(divider.props.tabindex, 0)
  divider.props.onKeydown({ key: 'ArrowUp', preventDefault() {} })
  divider.props.onKeydown({ key: 'End', preventDefault() {} })
  assert.deepEqual(values, [50, 80])
  const target = { parentElement: { getBoundingClientRect: () => ({ top: 100, left: 50, height: 500, width: 1000 }) }, setPointerCapture() {}, hasPointerCapture: () => false }
  divider.props.onPointerdown({ button: 0, pointerId: 1, currentTarget: target, preventDefault() {} })
  divider.props.onPointermove({ pointerId: 1, clientY: 350, clientX: 200 })
  divider.props.onPointermove({ pointerId: 1, clientY: 900, clientX: 200 })
  assert.deepEqual(values.slice(-2), [50, 80])
  divider.props.onPointercancel({ pointerId: 1, currentTarget: target })
  divider.props.onPointermove({ pointerId: 1, clientY: 200 })
  assert.equal(values.at(-1), 80)
  page.unmount()
})

test('Run code can reveal the existing Terminal beside Instructions from an expanded preview', async () => {
  browser()
  const page = await mount(Build)
  const terminal = findAll(page.root, el => el.type === 'iframe')[0]
  await click(page.root, 'App Preview')
  await click(page.root, 'Expand app preview')
  assert.equal(typeof page.vm.showTerminal, 'function')
  await page.vm.showTerminal()
  await flush()
  assert.equal(page.vm.expandedPanel, null)
  assert.equal(button(page.root, 'Terminal').props['aria-selected'], true)
  assert.equal(findAll(page.root, el => el.type === 'iframe')[0], terminal)
  page.unmount()
})
