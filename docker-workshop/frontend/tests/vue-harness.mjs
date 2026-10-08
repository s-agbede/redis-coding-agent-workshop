import { readFile } from 'node:fs/promises'
import { parse, compileScript } from '@vue/compiler-sfc'
import { compile } from '@vue/compiler-dom'
import ts from 'typescript'
import * as Vue from 'vue'

// Use Vue's renderer/compiler directly; browser-only child frames are replaced
// at their boundaries, while page templates and event handlers remain real.
export async function component(path, imports = {}) {
  const { descriptor } = parse(await readFile(new URL(path, import.meta.url), 'utf8'))
  const script = compileScript(descriptor, { id: path, inlineTemplate: true })
  const compiled = ts.transpileModule(script.content, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText
  const module = { exports: {} }
  const require = name => {
    if (name === 'vue') return Vue
    if (!(name in imports)) throw new Error(`Missing test boundary: ${name}`)
    return name.endsWith('.vue') ? { default: imports[name] } : imports[name]
  }
  new Function('require', 'module', 'exports', compiled)(require, module, module.exports)
  const result = module.exports.default
  if (!descriptor.scriptSetup) result.render = new Function('Vue', compile(descriptor.template.content, { mode: 'function', prefixIdentifiers: true }).code)(Vue)
  return result
}

function node(type, text = '') {
  return { type, text, props: {}, style: {}, children: [], parent: null, scrollTop: 0, focused: false, scrolledIntoView: false, scrollIntoView() { this.scrolledIntoView = true }, value: '', selectionStart: 0, selectionEnd: 0, listeners: {}, addEventListener(name, callback) { this.listeners[name] = callback }, setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end }, focus() { this.focused = true } }
}

export const renderer = Vue.createRenderer({
  createElement: tag => node(tag), createText: text => node('#text', text), createComment: text => node('#comment', text),
  setText: (element, text) => { element.text = text },
  setElementText: (element, text) => { element.text = text; element.children = [] },
  patchProp: (element, key, previous, next) => { element.props[key] = next; if (key === 'value') element.value = next },
  insert(element, parent, anchor = null) {
    if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1)
    const index = anchor ? parent.children.indexOf(anchor) : -1
    parent.children.splice(index < 0 ? parent.children.length : index, 0, element)
    element.parent = parent
  },
  remove(element) { element.parent?.children.splice(element.parent.children.indexOf(element), 1) },
  parentNode: element => element.parent,
  nextSibling: element => element.parent?.children[element.parent.children.indexOf(element) + 1] || null
})

export async function flush() { await new Promise(resolve => setImmediate(resolve)); await Vue.nextTick() }
export async function mount(component, props = {}, globals = {}) {
  const root = node('root')
  const app = renderer.createApp(component, props)
  Object.assign(app.config.globalProperties, globals)
  const vm = app.mount(root)
  await flush()
  return { root, vm, unmount: () => app.unmount() }
}
export function findAll(root, predicate) { return [root, ...root.children.flatMap(child => findAll(child, () => true))].filter(predicate) }
export function textOf(root) { return root.text + (root.props.innerHTML || '') + root.children.map(textOf).join(' ') }
export const Stub = { render: () => Vue.h('div') }
