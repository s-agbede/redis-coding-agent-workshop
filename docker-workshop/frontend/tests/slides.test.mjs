import assert from 'node:assert/strict'
import { test } from 'node:test'
import { component, mount, findAll, textOf, flush } from './vue-harness.mjs'
import { splitSlides } from '../src/utils/slides.js'
const Slides = await component('../src/components/LessonSlides.vue', {
  '../utils/slides': { splitSlides },
  '../utils/markdown': { markdownToHtml: value => `<p>${value}</p>` },
  '../utils/basePath': { getBasePath: () => '/guide' }
})
const button = (page, text) => findAll(page.root, el => el.type === 'button' && el.text === text)[0]

test('slide separators respect fenced code blocks', () => {
  assert.deepEqual(splitSlides('# One\n```text\n---\n```\n---\n# Two'), ['# One\n```text\n---\n```', '# Two'])
  assert.deepEqual(splitSlides('\r\n# One\r\n---\r\n# Two'), ['# One', '# Two'])
})
test('embedded slides navigate, switch to text and exit focus mode', async () => {
  let url
  globalThis.fetch = async path => { url = path; return new Response('# First\n---\n# Second') }
  const page = await mount(Slides, { src: '/slides/01-recap.md' })
  assert.equal(url, '/guide/slides/01-recap.md')
  assert.match(textOf(page.root), /First/)
  assert.equal(button(page, 'Previous').props.disabled, true)
  await button(page, 'Next').props.onClick(); await flush()
  assert.match(textOf(page.root), /Second/)
  assert.equal(button(page, 'Next').props.disabled, true)
  await button(page, 'Read text').props.onClick(); await flush()
  assert.match(textOf(page.root), /First/)
  assert.match(textOf(page.root), /Second/)
  await button(page, 'Focus mode').props.onClick(); await flush()
  assert.ok(button(page, 'Exit focus'))
  assert.equal(findAll(page.root, el => el.type === 'section')[0].props.role, 'dialog')
  assert.equal(findAll(page.root, el => el.type === 'section')[0].props['aria-modal'], 'true')
  page.vm.handleKeys({ key: 'Escape', preventDefault() {} }); await flush()
  assert.ok(button(page, 'Focus mode'))
  assert.equal(button(page, 'Focus mode').focused, true)
  assert.equal(findAll(page.root, el => el.type === 'section')[0].props.role, 'region')
  page.unmount()
})
test('slide failure leaves a clear retry path', async () => {
  globalThis.fetch = async () => new Response('', { status: 503 })
  const page = await mount(Slides, { src: '/slides/01-recap.md' })
  assert.match(textOf(page.root), /Exercises below remain available/)
  globalThis.fetch = async () => new Response('# Recovered')
  await button(page, 'Retry slides').props.onClick(); await flush()
  assert.match(textOf(page.root), /Recovered/)
  page.unmount()
})
test('the whole deck can be downloaded as a PDF', async () => {
  globalThis.fetch = async () => new Response('# First')
  const page = await mount(Slides, { src: '/slides/01-recap.md' })
  const link = findAll(page.root, el => el.type === 'a' && /Download slides/.test(el.text))[0]
  assert.ok(link)
  assert.equal(link.props.href, '/guide/slides/agent-memory-workshop-slides.pdf')
  assert.equal(link.props.download, 'agent-memory-workshop-slides.pdf')
  page.unmount()
})
