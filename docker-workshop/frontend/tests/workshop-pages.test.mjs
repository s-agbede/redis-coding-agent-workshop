import assert from 'node:assert/strict'
import { test } from 'node:test'
import { component, mount, findAll, textOf, flush, Stub } from './vue-harness.mjs'
import { SelfChecks } from '../src/selfChecks.ts'
import * as lessonContent from '../src/lessonContent.ts'
import * as editorText from '../src/editorText.ts'
import { EditorSession } from '../src/editorSession.ts'
import { renderMarkdown } from '../../vendor/workshop-front-end-components/src/content-renderer/markdown.js'

const memoryStorage = () => {
  const map = new Map()
  return { getItem: key => map.get(key) ?? null, setItem: (key, value) => map.set(key, value) }
}
const lessons = [
  { id: 'one', file: 'one.md', title: 'First lesson', content: 'Try it', editorFile: 'first_call.py' },
  { id: 'two', file: 'two.md', title: 'Second lesson', content: 'Prove it', editorFile: 'tools.py' }
]
const config = {
  loadWorkshopConfig: async () => ({}), getPhaseStepTitles: () => ['Welcome', 'Build'],
  getEnabledPhases: () => [{ id: 'welcome', route: '/' }, { id: 'build', route: '/build' }],
  isPhaseEnabled: () => true, getNextPhase: () => ({ route: '/build' })
}
const LessonContent = await component('../src/components/LessonContent.vue', {
  '../lessonContent': lessonContent,
  '../utils/basePath': { getApiUrl: path => path }
})
const buildImports = {
  '@redis-workshop/components/components/WorkshopHeader.vue': Stub,
  '../components/BuildPanel.vue': Stub,
  '../components/PanelToggle.vue': Stub,
  '../components/PanelDivider.vue': Stub,
  '../components/LessonContent.vue': LessonContent,
  '../utils/demoSteps': { loadAllDemoSteps: async () => lessons },
  '../utils/buildSteps': { loadAllBuildSteps: async () => lessons, markdownToHtml: content => `<p>${content}</p>` },
  '../utils/workshopConfig': config,
  '../selfChecks': { SelfChecks },
  '../utils/basePath': { getBasePath: () => '/hub/workshop/agent' }
}
const Build = await component('../src/views/Build.vue', buildImports)

function browserStorage() {
  globalThis.window = { localStorage: memoryStorage() }
  globalThis.sessionStorage = memoryStorage()
  globalThis.document = { addEventListener() {}, removeEventListener() {} }
}

test('lesson navigation resets the instructions and focuses the new heading after render', async () => {
  browserStorage()
  const page = await mount(Build)
  const panel = findAll(page.root, el => el.props.class === 'build-instructions')[0]
  panel.scrollTop = 500
  await page.vm.goToStep(1)
  await flush()
  assert.equal(panel.scrollTop, 0)
  const heading = findAll(page.root, el => el.type === 'h2' && el.text === 'Second lesson')[0]
  assert.equal(heading.focused, true)
  page.unmount()
})

test('lessons have no evidence forms and leave previous saved records untouched', async () => {
  browserStorage()
  const saved = '{"one.md":{"notes":"Earlier learner notes"}}'
  window.localStorage.setItem('coding-agent-build-self-checks-v2', saved)
  const page = await mount(Build)
  assert.equal(findAll(page.root, el => el.type === 'input' && el.props.type === 'checkbox').length, 0)
  assert.equal(findAll(page.root, el => el.type === 'textarea').length, 0)
  assert.doesNotMatch(textOf(page.root), /Your evidence|View my progress|Component map/)
  await page.vm.goToStep(1)
  assert.equal(window.localStorage.getItem('coding-agent-build-self-checks-v2'), saved)
  page.unmount()
})

test('the last lesson returns to welcome without claiming learner success', async () => {
  browserStorage()
  const routes = []
  const page = await mount(Build, {}, { $router: { push: route => routes.push(route) } })
  await page.vm.goToStep(1)
  const finish = findAll(page.root, el => el.type === 'button' && el.text.trim() === 'Back to welcome')[0]
  assert.ok(finish)
  await finish.props.onClick()
  assert.deepEqual(routes, ['/'])
  assert.doesNotMatch(textOf(page.root), /Your progress|Practical checks:/)
  page.unmount()
})

test('welcome shows outcomes and starts directly with the workshop', async () => {
  const Welcome = await component('../src/views/Welcome.vue', {
    '../utils/pageContent': { loadWelcomeContent: async () => ({ title: 'Workshop', estimatedMinutes: 90, htmlContent: '<h2>What you will build</h2><p>A coding agent.</p>' }) },
    '../utils/workshopConfig': config,
    '../components/LessonContent.vue': LessonContent
  })
  const routes = []
  const page = await mount(Welcome, {}, { $router: { push: route => routes.push(route) } })
  const text = textOf(page.root)
  assert.match(text, /Time to allow/)
  assert.match(text, /What you will build/)
  await page.vm.startWorkshop()
  assert.deepEqual(routes, ['/build'])
  page.unmount()
})

test('lesson copy control uses the code text and exposes clipboard failure in the page', async () => {
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { clipboard: { writeText: async () => { throw new Error('denied') } } } })
  const page = await mount(LessonContent, { html: '<pre><code>    reader(**args)</code></pre>' })
  const htmlNode = findAll(page.root, el => el.props.innerHTML)[0]
  const code = { textContent: '    reader(**args)' }
  const error = { textContent: '', hidden: true }
  const button = { textContent: 'Copy code', parentElement: { querySelector: selector => selector === 'pre code' ? code : error } }
  const event = { target: { closest: selector => selector === 'button[data-copy-code]' ? button : null } }
  await htmlNode.props.onClick(event)
  await flush()
  assert.equal(error.hidden, false)
  assert.match(error.textContent, /select the code and copy/i)
  assert.equal(button.textContent, 'Retry copy')
  let copied
  navigator.clipboard.writeText = async text => { copied = text }
  await htmlNode.props.onClick(event)
  await flush()
  assert.equal(copied, code.textContent)
  assert.equal(error.hidden, true)
  assert.equal(button.textContent, 'Copied')
  page.unmount()
})

function runClickFixture(command) {
  const error = { textContent: '', hidden: true }
  const status = { textContent: '', hidden: true }
  const code = { textContent: command }
  const button = { disabled: false, textContent: 'Run code', parentElement: {
    querySelector: selector => selector === 'pre code' ? code : selector === '[data-run-status]' ? status : error
  } }
  const event = { target: { closest: selector => selector === 'button[data-run-code]' ? button : null } }
  return { error, status, button, event }
}

test('welcome Run code reveals its parent Terminal and direct welcome refuses dispatch', async () => {
  const Welcome = await component('../src/views/Welcome.vue', {
    '../utils/pageContent': { loadWelcomeContent: async () => ({ htmlContent: '<pre><code class="language-bash">uv run python check_setup.py</code></pre>' }) },
    '../utils/workshopConfig': config,
    '../components/LessonContent.vue': LessonContent
  })
  const { messages } = guideBrowser()
  let dispatches = 0
  globalThis.fetch = async () => { dispatches++; return new Response(JSON.stringify({ status: 'sent' })) }
  let page = await mount(Welcome)
  let html = findAll(page.root, el => el.props.innerHTML)[0]
  await html.props.onClick(runClickFixture('uv run python check_setup.py').event)
  assert.equal(dispatches, 1)
  assert.deepEqual(messages, [[{ type: 'show-workshop-terminal' }, 'http://localhost:8080']])
  page.unmount()
  window.parent = window
  page = await mount(Welcome)
  html = findAll(page.root, el => el.props.innerHTML)[0]
  const direct = runClickFixture('uv run python check_setup.py')
  await html.props.onClick(direct.event)
  assert.equal(dispatches, 1)
  assert.equal(direct.error.hidden, false)
  assert.match(direct.error.textContent, /open the workbench/i)
  page.unmount()
})

test('Run code reveals Terminal, prevents double clicks and displays dispatch status', async () => {
  const originalFetch = globalThis.fetch
  let finish
  let requests = 0
  let reveals = 0
  globalThis.fetch = () => { requests++; return new Promise(resolve => { finish = resolve }) }
  const page = await mount(LessonContent, { html: '<pre><code class="language-bash">pwd</code></pre>', onShowTerminal: () => { reveals++ } })
  try {
    const node = findAll(page.root, el => el.props.innerHTML)[0]
    const { button, status, error, event } = runClickFixture('pwd')
    const running = node.props.onClick(event)
    assert.equal(reveals, 1)
    assert.equal(button.disabled, true)
    await node.props.onClick(event)
    assert.equal(requests, 1)
    finish(new Response(JSON.stringify({ status: 'sent' })))
    await running
    assert.equal(button.disabled, false)
    assert.equal(button.textContent, 'Run code')
    assert.equal(error.hidden, true)
    assert.equal(status.hidden, false)
    assert.match(status.textContent, /Sent to Terminal/)
  } finally { globalThis.fetch = originalFetch; page.unmount() }
})

test('busy dispatch errors remain visible next to the command', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Exit the running program first.' }), { status: 409 })
  const page = await mount(LessonContent, { html: '<pre><code class="language-bash">pwd</code></pre>' })
  try {
    const node = findAll(page.root, el => el.props.innerHTML)[0]
    const { button, status, error, event } = runClickFixture('pwd')
    await node.props.onClick(event)
    assert.equal(error.hidden, false)
    assert.match(error.textContent, /Exit the running program/)
    assert.equal(status.hidden, true)
    assert.equal(button.disabled, false)
  } finally { globalThis.fetch = originalFetch; page.unmount() }
})

test('standalone guide refuses to run into a terminal the learner cannot see', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = () => { throw new Error('Must not dispatch') }
  const page = await mount(LessonContent, { html: '<pre><code class="language-bash">pwd</code></pre>', terminalAvailable: false })
  try {
    const node = findAll(page.root, el => el.props.innerHTML)[0]
    const { error, event } = runClickFixture('pwd')
    await node.props.onClick(event)
    assert.equal(error.hidden, false)
    assert.match(error.textContent, /open the workbench/i)
  } finally { globalThis.fetch = originalFetch; page.unmount() }
})

test('mobile navigation brings the rendered heading into document view, including initial load', async () => {
  browserStorage()
  window.matchMedia = () => ({ matches: true })
  const page = await mount(Build)
  let heading = findAll(page.root, el => el.type === 'h2' && el.text === 'First lesson')[0]
  assert.equal(heading.scrolledIntoView, true)
  heading.scrolledIntoView = false
  await page.vm.goToStep(1)
  heading = findAll(page.root, el => el.type === 'h2' && el.text === 'Second lesson')[0]
  assert.equal(heading.scrolledIntoView, true)
  page.unmount()
})

test('only the current lesson content and file action appear beside navigation', async () => {
  browserStorage()
  const page = await mount(Build)
  assert.equal(findAll(page.root, el => el.props.class === 'component-reference').length, 0)
  assert.match(textOf(page.root), /Open first_call.py/)
  await page.vm.goToStep(1)
  assert.match(textOf(page.root), /Open tools.py/)
  assert.doesNotMatch(textOf(page.root), /Open main.py|Your role:/)
  page.unmount()
})

test('clicking a file in a lesson opens it through the workspace and saves previous edits', async () => {
  browserStorage()
  Object.assign(window, { addEventListener() {}, removeEventListener() {} })
  const documents = new Map([['first_call.py', '# first'], ['tools.py', '# reader']])
  const operations = []
  globalThis.fetch = async (url, init) => {
    const response = data => ({ ok: true, json: async () => data })
    if (url === '/api/editor/files') return response([...documents.keys()].map(path => ({ path })))
    if (init?.method === 'POST') {
      const { path, content } = JSON.parse(init.body)
      operations.push(`save ${path}`)
      documents.set(path, content)
      return response({})
    }
    const path = new URL(url, 'http://local').searchParams.get('path')
    operations.push(`read ${path}`)
    return response({ path, content: documents.get(path), language: 'python' })
  }
  const CodeEditor = await component('../src/components/CodeEditor.vue', {
    '../editorSession': { EditorSession }, '../editorText': editorText,
    '../utils/basePath': { getApiUrl: path => path }, 'vue-router': { onBeforeRouteLeave() {} }
  })
  const BuildPanel = await component('../src/components/BuildPanel.vue', {
    './CodeEditor.vue': CodeEditor, './AppEmbed.vue': Stub,
    './PanelToggle.vue': Stub, './PanelDivider.vue': Stub,
    '../utils/basePath': { getApiUrl: path => path }
  })
  const pageComponent = await component('../src/views/Build.vue', {
    ...buildImports, '../components/BuildPanel.vue': BuildPanel,
    '../utils/buildSteps': { loadAllBuildSteps: async () => [{ ...lessons[0], content: 'Open **tools.py**.' }], markdownToHtml: renderMarkdown }
  })
  const page = await mount(pageComponent)
  const htmlNode = findAll(page.root, el => el.props.innerHTML?.includes('tools.py'))[0]
  assert.match(htmlNode.props.innerHTML, /data-open-file="tools.py"/)
  const field = findAll(page.root, el => el.props['aria-label'] === 'Contents of first_call.py')[0]
  field.value = '# my code'
  field.props.onInput({ target: field })
  const fileButton = { dataset: { openFile: 'tools.py' } }
  page.vm.expandedPanel = 'instructions'
  await htmlNode.props.onClick({ target: { closest: selector => selector === 'button[data-open-file]' ? fileButton : null } })
  await flush()
  assert.equal(page.vm.selectedFile, 'tools.py')
  assert.equal(page.vm.expandedPanel, null, 'opening a file reveals the workspace beside the instructions')
  assert.equal(field.value, '# reader')
  assert.equal(field.focused, true)
  assert.equal(documents.get('first_call.py'), '# my code')
  assert.deepEqual(operations, ['read first_call.py', 'save first_call.py', 'read tools.py'])
  page.unmount()
})

const guideImports = {
  ...buildImports,
  '../utils/basePath': { getBasePath: () => '/guide' },
  '../utils/buildSteps': { loadAllBuildSteps: async () => lessons.map(step => ({ ...step, content: 'Inspect `tools.py`.\n\n<details>\n<summary>Answer</summary>\n\nExplain it.\n</details>' })), markdownToHtml: renderMarkdown }
}
const GuideBuild = await component('../src/views/Build.vue', guideImports)
function guideBrowser() {
  browserStorage()
  const messages = []
  window.location = { pathname: '/guide/build', origin: 'http://localhost:8080' }
  window.parent = { postMessage: (...args) => messages.push(args) }
  const requests = []
  globalThis.fetch = async url => {
    requests.push(url)
    return { ok: true, json: async () => [{ path: 'tools.py' }, { path: 'first_call.py' }, { path: 'main.py' }, { path: 'ui.py' }, { path: 'agent.py' }] }
  }
  return { messages, requests }
}

test('embedded guide has instructions without an editor, terminal, divider or expansion controls', async () => {
  guideBrowser()
  const page = await mount(GuideBuild)
  assert.equal(findAll(page.root, el => el.props.class === 'build-interactive-panel').length, 0)
  assert.equal(findAll(page.root, el => el.props.class === 'workspace-divider').length, 0)
  assert.equal(findAll(page.root, el => el.props.label === 'instructions').length, 0)
  const panel = findAll(page.root, el => el.props.class === 'build-instructions')[0]
  assert.equal(panel.props.style?.flexBasis, undefined)
  assert.match(textOf(page.root), /First lesson/)
  page.unmount()
})

test('running in the guide asks the parent to reveal Terminal without navigating', async () => {
  const { messages } = guideBrowser()
  const page = await mount(GuideBuild)
  assert.equal(typeof page.vm.showTerminal, 'function')
  assert.equal(page.vm.terminalAvailable, true)
  await page.vm.showTerminal()
  assert.deepEqual(messages, [[{ type: 'show-workshop-terminal' }, 'http://localhost:8080']])
  page.unmount()
  window.parent = window
  const direct = await mount(GuideBuild)
  assert.equal(direct.vm.terminalAvailable, false)
  direct.unmount()
})

test('guide filename and source buttons use the root file list and dispatch to the same-origin parent', async () => {
  const { messages, requests } = guideBrowser()
  const page = await mount(GuideBuild)
  assert.deepEqual(requests, ['/api/editor/files'])
  const htmlNode = findAll(page.root, el => el.props.innerHTML?.includes('tools.py'))[0]
  assert.match(htmlNode.props.innerHTML, /data-open-file="tools.py"/)
  const fileButton = { dataset: { openFile: 'tools.py' } }
  await htmlNode.props.onClick({ target: { closest: selector => selector === 'button[data-open-file]' ? fileButton : null } })
  const sourceButton = findAll(page.root, el => el.type === 'button' && el.text === 'Open first_call.py')[0]
  await sourceButton.props.onClick()
  assert.deepEqual(messages, [
    [{ type: 'open-workshop-file', path: 'tools.py' }, 'http://localhost:8080'],
    [{ type: 'open-workshop-file', path: 'first_call.py' }, 'http://localhost:8080']
  ])
  await page.vm.openFile('../secret')
  assert.equal(messages.length, 2)
  assert.match(textOf(page.root), /not available in the workspace/i)
  page.unmount()
})

test('guide preserves lesson position across reloads with answers closed', async () => {
  guideBrowser()
  window.localStorage.setItem('coding-agent-build-self-checks-v1', '{"one.md":true}')
  let page = await mount(GuideBuild)
  const content = findAll(page.root, el => el.props.innerHTML?.includes('Answer'))[0]
  assert.doesNotMatch(content.props.innerHTML, /<details open/)
  await page.vm.goToStep(1)
  page.unmount()
  page = await mount(GuideBuild)
  assert.equal(page.vm.currentBuildStep, 1)
  assert.equal(window.localStorage.getItem('coding-agent-build-self-checks-v1'), '{"one.md":true}')
  assert.equal(window.localStorage.getItem('coding-agent-build-self-checks-v2'), null)
  page.unmount()
})

test('wide embedded guide scrolls each new lesson into document view', async () => {
  guideBrowser()
  window.matchMedia = () => ({ matches: false })
  const page = await mount(GuideBuild)
  let heading = findAll(page.root, el => el.type === 'h2' && el.text === 'First lesson')[0]
  assert.equal(heading.scrolledIntoView, true, 'initial guide lesson is visible at desktop width')
  heading.scrolledIntoView = false
  await page.vm.goToStep(1)
  heading = findAll(page.root, el => el.type === 'h2' && el.text === 'Second lesson')[0]
  assert.equal(heading.scrolledIntoView, true, 'next lesson scrolls the guide document')
  page.unmount()
})

test('wide standalone navigation keeps scrolling inside the instruction panel', async () => {
  browserStorage()
  window.matchMedia = () => ({ matches: false })
  const page = await mount(Build)
  const panel = findAll(page.root, el => el.props.class === 'build-instructions')[0]
  panel.scrollTop = 500
  await page.vm.goToStep(1)
  const heading = findAll(page.root, el => el.type === 'h2' && el.text === 'Second lesson')[0]
  assert.equal(panel.scrollTop, 0)
  assert.equal(heading.scrolledIntoView, false)
  page.unmount()
})

test('direct guide access offers the full workbench and file actions explain how to open it', async () => {
  const { messages } = guideBrowser()
  window.parent = window
  const App = await component('../src/App.vue', { './utils/basePath': { getBasePath: () => '/guide' } })
  App.components = { RouterView: Stub }
  const app = await mount(App)
  const link = findAll(app.root, el => el.type === 'a' && el.props.href === '/')[0]
  assert.ok(link, 'direct guide needs an open-workbench link')
  assert.match(textOf(link), /Open.*workbench/i)
  app.unmount()
  const page = await mount(GuideBuild)
  await page.vm.openFile('tools.py')
  assert.match(textOf(page.root), /open the workbench/i)
  assert.deepEqual(messages, [])
  page.unmount()
})

test('unavailable guide file list leaves lessons usable and shows a retry control', async () => {
  guideBrowser()
  globalThis.fetch = async () => ({ ok: false, status: 503 })
  const page = await mount(GuideBuild)
  assert.match(textOf(page.root), /Could not load workspace files/)
  assert.match(textOf(page.root), /First lesson/)
  const retry = findAll(page.root, el => el.type === 'button' && el.text === 'Retry file list')[0]
  assert.ok(retry)
  globalThis.fetch = async () => ({ ok: true, json: async () => [{ path: 'tools.py' }] })
  await retry.props.onClick()
  await flush()
  assert.deepEqual([...page.vm.filePaths], ['tools.py'])
  assert.doesNotMatch(textOf(page.root), /Could not load workspace files/)
  page.unmount()
})

test('Workshop Home stays within the guide in review, demo and build', async () => {
  guideBrowser()
  const WorkshopHeader = await component('../../vendor/workshop-front-end-components/src/components/WorkshopHeader.vue')
  const imports = { ...guideImports, '@redis-workshop/components/components/WorkshopHeader.vue': WorkshopHeader }
  const Guide = await component('../src/views/Build.vue', imports)
  const Review = await component('../src/views/Review.vue', {
    '@redis-workshop/components/components/WorkshopHeader.vue': WorkshopHeader,
    '../utils/basePath': { getBasePath: () => '/guide' },
    '../utils/pageContent': { loadReviewContent: async () => ({ htmlContent: '<p>Concepts</p>' }) },
    '../utils/workshopConfig': { ...config, getPreviousPhase: () => ({ route: '/', title: 'Welcome' }) }
  })
  for (const [view, props] of [[Review, {}], [Guide, { phase: 'demo' }], [Guide, { phase: 'build' }]]) {
    const page = await mount(view, props)
    const home = findAll(page.root, el => el.type === 'a' && el.props.class === 'back-link')[0]
    assert.equal(home.props.href, '/guide/', 'header home must not nest the workbench inside Instructions')
    page.unmount()
  }
  browserStorage()
  const Standalone = await component('../src/views/Build.vue', {
    ...buildImports, '@redis-workshop/components/components/WorkshopHeader.vue': WorkshopHeader
  })
  const page = await mount(Standalone)
  assert.equal(findAll(page.root, el => el.type === 'a' && el.props.class === 'back-link')[0].props.href, '/')
  page.unmount()
})


test('new curriculum ignores old numeric lesson positions and restores by file name', async () => {
  browserStorage()
  sessionStorage.setItem('coding-agent-build-step', '1')
  let page = await mount(Build)
  assert.equal(page.vm.currentBuildStep, 0)
  await page.vm.goToStep(1)
  assert.equal(sessionStorage.getItem('coding-agent-workshop-lesson-v3'), 'two.md')
  page.unmount()
  page = await mount(Build)
  assert.equal(page.vm.currentBuildStep, 1)
  page.unmount()
})
