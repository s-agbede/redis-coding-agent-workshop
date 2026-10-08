const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const root = resolve(__dirname, '..');
const script = readFileSync(resolve(root, 'assets/script.js'), 'utf8');
const origin = 'http://localhost:8080';

function nativeFileTarget(url) {
  const payload = new Map(JSON.parse(url.searchParams.get('payload')));
  assert.equal(payload.get('gotoLineMode'), 'true');
  const target = new URL(payload.get('openFile'));
  assert.equal(target.protocol, 'vscode-remote:');
  assert.equal(target.host, new URL(origin).host);
  return target.pathname;
}

function harness() {
  const listeners = {};
  const elements = new Map();
  const makeElement = () => ({
    style: {}, dataset: {}, attributes: {}, children: [],
    classList: { toggle() {}, add() {}, remove() {} },
    setAttribute(name, value) { this.attributes[name] = value; },
    querySelector(selector) { return this.children[selector]; },
  });
  for (const id of ['sidebar', 'panel-vscode', 'panel-terminal', 'panel-app']) {
    const section = makeElement();
    const frame = makeElement();
    frame.contentWindow = {};
    frame.src = id === 'panel-vscode' ? `${origin}/vscode/?folder=/workspace` : '';
    frame.getAttribute = (name) => frame[name];
    section.children.iframe = frame;
    section.children['.panel-loading'] = makeElement();
    const button = makeElement();
    button.children.i = makeElement();
    section.children['.maximize-btn'] = button;
    elements.set(id, section);
  }
  for (const id of ['rightStack', 'verticalResizer', 'container', 'menu-sidebar', 'menu-vscode', 'menu-terminal', 'menu-app']) elements.set(id, makeElement());
  const document = {
    getElementById: (id) => elements.get(id),
    querySelectorAll: (selector) => selector === 'iframe' ? [...elements.values()].flatMap(e => e.children.iframe ? [e.children.iframe] : []) : [],
  };
  const context = vm.createContext({ URL, URLSearchParams, document, console, setTimeout,
    window: { location: { origin }, addEventListener: (name, callback) => { listeners[name] = callback; } },
  });
  vm.runInContext(readFileSync(resolve(root, 'config.js'), 'utf8'), context);
  vm.runInContext(script.replace(/init\(\);\s*$/, ''), context);
  vm.runInContext(`panelState = {vscode:{visible:true},terminal:{visible:true},app:{visible:false}};
    rebuildHorizontalResizers = () => {};
    buildPanels = () => { throw new Error('Panel rebuild destroys iframe sessions'); };
    buildMenu = () => {};`, context);
  return { context, elements, listeners, run: (code) => vm.runInContext(code, context) };
}

function fileUrl(data) {
  const { context } = harness();
  assert.equal(typeof context.getWorkshopFileUrl, 'function', 'a safe file URL resolver must exist');
  return context.getWorkshopFileUrl(data, origin);
}

test('builds native code-server file payload URLs for relative and nested workspace files', () => {
  for (const path of ['agent.py', 'checkpoints/stage1_chat.py', 'capstone/app.py']) {
    const url = new URL(fileUrl({ type: 'open-workshop-file', path }), origin);
    assert.equal(url.pathname, '/vscode/');
    assert.equal(url.searchParams.get('folder'), '/workspace');
    assert.equal(nativeFileTarget(url), `/workspace/${path}:1:1`);
  }
});

test('rejects malformed, absolute, traversal and encoded traversal paths', () => {
  for (const path of [null, 10, '', '/etc/passwd', '../agent.py', 'capstone/../../a', 'a/./b', 'a//b', 'a\\b', '%2e%2e/a', 'a%2fb', 'https://evil.test/a', 'a?x=y', 'a#b', 'a\n.py']) {
    assert.equal(fileUrl({ type: 'open-workshop-file', path }), null, String(path));
  }
});

test('legacy links require same origin and a strict workspace boundary', () => {
  const href = '/vscode/?folder=/workspace&goto=/workspace/checkpoints/stage1_chat.py:3:2';
  const url = new URL(fileUrl({ type: 'open-vscode-file', href }), origin);
  assert.equal(nativeFileTarget(url), '/workspace/checkpoints/stage1_chat.py:3:2');
  for (const href of ['https://evil.test/vscode/?goto=/workspace/agent.py', '/vscode/?goto=/workspace-other/agent.py', '/vscode/?goto=/workspace/../etc/passwd', '/vscode/?folder=/etc&goto=/workspace/a', '/vscode/?goto=/workspace/%252e%252e/a', '/vscode/?goto=/workspace/a&goto=/workspace/b', '/other/?goto=/workspace/a', 'http://[', null]) {
    assert.equal(fileUrl({ type: 'open-vscode-file', href }), null, String(href));
  }
});

test('hiding and restoring Instructions preserves every iframe and source', () => {
  const { elements, run } = harness();
  const frames = ['sidebar', 'panel-vscode', 'panel-terminal'].map(id => elements.get(id).children.iframe);
  const sources = frames.map(frame => frame.src);
  run('toggleSidebarVisibility(false); toggleSidebarVisibility(true);');
  assert.deepEqual(frames.map(frame => frame.src), sources);
  assert.equal(elements.get('sidebar').style.display, '');
});

test('Instructions and Code expand across the workbench and restore without rebuilding', () => {
  const { elements, run, context } = harness();
  assert.equal(typeof context.toggleMaximize, 'function');
  const frame = elements.get('panel-vscode').children.iframe;
  run("toggleMaximize('instructions')");
  assert.equal(elements.get('rightStack').style.display, 'none');
  assert.equal(elements.get('sidebar').style.display, '');
  run("toggleMaximize('instructions'); toggleMaximize('vscode')");
  assert.equal(elements.get('sidebar').style.display, 'none');
  assert.equal(elements.get('panel-terminal').style.display, 'none');
  run("toggleMaximize('vscode')");
  assert.equal(elements.get('sidebar').style.display, '');
  assert.equal(elements.get('panel-terminal').style.display, '');
  assert.equal(elements.get('panel-vscode').children.iframe, frame);
});

test('accepts file messages only from the same-origin Instructions frame', () => {
  const { run, listeners, elements } = harness();
  run('setupPanelMessageHandlers()');
  const frame = elements.get('panel-vscode').children.iframe;
  const initial = frame.src;
  const data = { type: 'open-workshop-file', path: 'agent.py' };
  listeners.message({ origin: 'https://evil.test', source: elements.get('sidebar').children.iframe.contentWindow, data });
  listeners.message({ origin, source: {}, data });
  assert.equal(frame.src, initial);
  listeners.message({ origin, source: elements.get('sidebar').children.iframe.contentWindow, data });
  assert.equal(nativeFileTarget(new URL(frame.src, origin)), '/workspace/agent.py:1:1');
});

test('Run code reveals Terminal and Instructions while preserving all iframe sessions', () => {
  const { run, listeners, elements } = harness();
  const ids = ['sidebar', 'panel-vscode', 'panel-terminal'];
  const frames = ids.map(id => elements.get(id).children.iframe);
  const sources = frames.map(frame => frame.src);
  run("setupPanelMessageHandlers(); panelState.terminal.visible = false; sidebarVisible = false; maximizedPanelId = 'vscode'; updatePanelVisibility();");
  const data = { type: 'show-workshop-terminal' };
  listeners.message({ origin: 'https://evil.test', source: frames[0].contentWindow, data });
  listeners.message({ origin, source: {}, data });
  assert.equal(elements.get('panel-terminal').style.display, 'none');
  listeners.message({ origin, source: frames[0].contentWindow, data });
  assert.equal(elements.get('panel-terminal').style.display, '');
  assert.equal(elements.get('sidebar').style.display, '');
  assert.deepEqual(ids.map(id => elements.get(id).children.iframe), frames);
  assert.deepEqual(frames.map(frame => frame.src), sources);
});

test('explicit file links reopen their target after an internal editor change leaves iframe URL unchanged', () => {
  const { run, elements, context } = harness();
  assert.equal(typeof context.openWorkshopFile, 'function');
  const frame = elements.get('panel-vscode').children.iframe;
  let navigations = 0;
  let source = frame.src;
  Object.defineProperty(frame, 'src', { get: () => source, set: value => { navigations += 1; source = value; } });
  run("maximizedPanelId = 'instructions'; panelState.vscode.visible = false; openWorkshopFile('agent.py');");
  // Native editor tab changes do not navigate the embedding iframe. Its src
  // still names agent.py even after a learner has selected tools.py internally.
  const sourceAfterFirstLink = frame.src;
  assert.equal(nativeFileTarget(new URL(sourceAfterFirstLink, origin)), '/workspace/agent.py:1:1');
  run("openWorkshopFile('agent.py');");
  assert.equal(navigations, 2, 'an explicit file link must not infer the active editor from iframe.src');
  assert.equal(frame.src, sourceAfterFirstLink);
  assert.equal(elements.get('panel-vscode').style.display, '');
  assert.equal(elements.get('sidebar').style.display, '');
});

test('public file opener accepts guide paths and validated legacy hrefs', () => {
  const { context, elements, run } = harness();
  run('setupPanelMessageHandlers()');
  context.window.openWorkshopFile('agent.py');
  const frame = elements.get('panel-vscode').children.iframe;
  assert.equal(nativeFileTarget(new URL(frame.src, origin)), '/workspace/agent.py:1:1');
  context.window.openWorkshopFile('/vscode/?folder=/workspace&goto=/workspace/tools.py:1:1');
  assert.equal(nativeFileTarget(new URL(frame.src, origin)), '/workspace/tools.py:1:1');
});

test('Instructions cannot be hidden when it is the last visible panel', () => {
  const { run, elements } = harness();
  run("togglePanelVisibility('vscode', false); togglePanelVisibility('terminal', false); toggleSidebarVisibility(false)");
  assert.equal(elements.get('sidebar').style.display, '');
});

test('late startup readiness response never overwrites a selected file URL', async () => {
  const { context, elements, run } = harness();
  const panel = elements.get('panel-vscode');
  const loading = panel.children['.panel-loading'];
  loading.parentElement = panel;
  loading.dataset.url = '/vscode/?folder=/workspace';
  let resolveFetch;
  context.fetch = () => new Promise(resolve => { resolveFetch = resolve; });
  context.loading = loading;
  run("loadPanelWithRetry(loading); openWorkshopFile('agent.py')");
  resolveFetch({ ok: true });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(nativeFileTarget(new URL(panel.children.iframe.src, origin)), '/workspace/agent.py:1:1');
});

test('resize supports arrow keys and restores frame interaction after pointer cancellation', () => {
  const { context, elements } = harness();
  const resizer = elements.get('verticalResizer');
  resizer.setPointerCapture = () => {};
  const frame = elements.get('panel-vscode').children.iframe;
  frame.style.pointerEvents = 'auto';
  let size = 200;
  context.setupResizeHandle(resizer, 'vertical', () => size, (initial, delta) => { size = initial + delta; });
  resizer.onkeydown({ key: 'ArrowRight', preventDefault() {} });
  assert.equal(size, 220);
  const source = frame.src;
  resizer.onpointerdown({ button: 0, clientX: 220, pointerId: 1, preventDefault() {} });
  assert.equal(frame.style.pointerEvents, 'none');
  resizer.onpointermove({ clientX: 270 });
  assert.equal(size, 270);
  resizer.onpointercancel();
  assert.equal(frame.style.pointerEvents, 'auto');
  assert.equal(frame.src, source);
});

test('legacy Docsify routes reveal Instructions without replacing editor or terminal frames', () => {
  const { context, elements, run } = harness();
  assert.equal(typeof context.openDocsRoute, 'function');
  const code = elements.get('panel-vscode').children.iframe;
  const terminal = elements.get('panel-terminal').children.iframe;
  const sources = [code.src, terminal.src];
  run("toggleSidebarVisibility(false); openDocsRoute('#/tutorials/first-call')");
  assert.equal(elements.get('sidebar').style.display, '');
  assert.equal(elements.get('sidebar').children.iframe.src, '/docs/#/tutorials/first-call');
  assert.deepEqual([code.src, terminal.src], sources);
  assert.doesNotThrow(() => context.openDocsRoute({}));
  context.openDocsRoute('https://evil.test/');
  assert.equal(elements.get('sidebar').children.iframe.src, '/docs/#/tutorials/first-call');
});

test('App Preview displays the controlled 503 startup page instead of retrying forever', async () => {
  const { context, elements, run } = harness();
  const panel = elements.get('panel-app');
  const loading = panel.children['.panel-loading'];
  loading.parentElement = panel;
  loading.dataset.url = '/app/';
  let hidden = false;
  loading.classList.add = value => { hidden = value === 'hidden'; };
  const retries = [];
  context.fetch = async () => ({ ok: false, status: 503 });
  context.setTimeout = callback => retries.push(callback);
  context.loading = loading;
  run('loadPanelWithRetry(loading)');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(panel.children.iframe.src, '/app/');
  assert.equal(hidden, true);
  assert.equal(retries.length, 0);
});

test('service errors outside the controlled App Preview fallback still retry', async () => {
  for (const [url, status] of [['/vscode/?folder=/workspace', 502], ['/vscode/?folder=/workspace', 503], ['/terminal/', 503], ['/app/', 502]]) {
    const { context, elements, run } = harness();
    const panel = elements.get('panel-vscode');
    const loading = panel.children['.panel-loading'];
    loading.parentElement = panel;
    loading.dataset.url = url;
    const initialSource = panel.children.iframe.src;
    const retries = [];
    context.fetch = async () => ({ ok: false, status });
    context.setTimeout = callback => retries.push(callback);
    context.loading = loading;
    run('loadPanelWithRetry(loading)');
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(panel.children.iframe.src, initialSource, `${url}: ${status}`);
    assert.equal(retries.length, 1, `${url}: ${status}`);
  }
});

test('Code readiness falls back to GET when code-server rejects HEAD with 405', async () => {
  const { context, elements, run } = harness();
  const panel = elements.get('panel-vscode');
  const loading = panel.children['.panel-loading'];
  loading.parentElement = panel;
  loading.dataset.url = '/vscode/?folder=/workspace';
  let hidden = false;
  loading.classList.add = value => { hidden = value === 'hidden'; };
  const methods = [];
  let bodyCancelled = false;
  const retries = [];
  context.fetch = async (url, options) => {
    methods.push(options.method);
    return options.method === 'HEAD'
      ? { ok: false, status: 405 }
      : { ok: true, status: 200, body: { cancel: async () => { bodyCancelled = true; } } };
  };
  context.setTimeout = callback => retries.push(callback);
  context.loading = loading;
  run('loadPanelWithRetry(loading)');
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(methods, ['HEAD', 'GET']);
  assert.equal(panel.children.iframe.src, '/vscode/?folder=/workspace');
  assert.equal(hidden, true);
  assert.equal(bodyCancelled, true);
  assert.equal(retries.length, 0);
});
