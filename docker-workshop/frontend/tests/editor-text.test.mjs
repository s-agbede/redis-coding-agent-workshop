import assert from 'node:assert/strict'
import { test } from 'node:test'
import * as editorText from '../src/editorText.ts'
const { indentText, enterText, TextHistory, visibleFiles } = editorText

const state = (content, start = 0, end = start) => ({ content, start, end })

test('Tab indents every selected line without replacing code', () => {
  const text = 'first()\nsecond()\nthird()'
  const result = indentText(state(text, 0, 17))
  assert.equal(result.content, '    first()\n    second()\nthird()')
  assert.equal(result.content.slice(result.start, result.end), 'first()\n    second()\n')
})

test('Shift+Tab outdents selected lines with spaces or tabs and keeps selection', () => {
  const result = indentText(state('    first()\n\tsecond()\n  third()', 4, 31), true)
  assert.equal(result.content, 'first()\nsecond()\nthird()')
  assert.equal(result.start, 0)
  assert.equal(result.end, result.content.length)
})

test('Tab at a caret inserts spaces and outdent at an unindented line does nothing', () => {
  assert.deepEqual(indentText(state('x = 1', 2)), state('x     = 1', 6))
  assert.deepEqual(indentText(state('x = 1', 2), true), state('x = 1', 2))
})

test('Enter carries indentation and adds a level after a Python colon', () => {
  assert.deepEqual(enterText(state('    if ready:', 13)), state('    if ready:\n        ', 22))
  assert.deepEqual(enterText(state('    call()', 10)), state('    call()\n    ', 15))
})

test('next exercise selects each numbered comment and wraps without stopping on error messages', () => {
  assert.equal(typeof editorText.nextExercise, 'function')
  const content = '# EXERCISE 1 - Send a message\nraise NotImplementedError("Complete exercise 1")\n# EXERCISE 2 - Read a file'
  const first = editorText.nextExercise(state(content))
  assert.equal(content.slice(first.start, first.end), 'EXERCISE 1 - Send a message')
  const second = editorText.nextExercise(first)
  assert.equal(content.slice(second.start, second.end), 'EXERCISE 2 - Read a file')
  assert.deepEqual(editorText.nextExercise(second), first)
  assert.equal(editorText.nextExercise(state('done')), null)
})

test('next exercise also finds markers in an older student workspace', () => {
  assert.equal(typeof editorText.nextExercise, 'function')
  const content = '"Fill BLANK 0"\n    # BLANK 0 - YOUR FIRST MODEL CALL'
  const result = editorText.nextExercise(state(content))
  assert.equal(content.slice(result.start, result.end), 'BLANK 0 - YOUR FIRST MODEL CALL')
})

test('undo restores typing and block indent, redo restores it, and new edits discard redo', () => {
  const history = new TextHistory(state('a', 1))
  history.record(state('ab', 2))
  history.record(state('ab', 0, 2))
  history.record(indentText(state('ab', 0, 2)))
  assert.deepEqual(history.undo(), state('ab', 0, 2))
  assert.deepEqual(history.undo(), state('a', 1))
  assert.deepEqual(history.redo(), state('ab', 0, 2))
  history.record(state('abc', 3))
  assert.equal(history.redo(), null)
})

test('workshop files are the default and any current non-workshop file stays visible', () => {
  const files = ['README.md', 'tools.py', 'first_call.py', 'solutions/agent.py', 'capstone/app.py'].map(path => ({ path }))
  assert.deepEqual(visibleFiles(files, false, '').map(file => file.path), ['first_call.py', 'tools.py', 'capstone/app.py'])
  assert.deepEqual(visibleFiles(files, false, 'README.md').map(file => file.path), ['first_call.py', 'tools.py', 'capstone/app.py', 'README.md'])
  assert.deepEqual(visibleFiles(files, true, ''), files)
})

test('indenting a selection starting on an empty first line keeps that line in the block', () => {
  assert.equal(indentText(state('\ncall()', 0, 7)).content, '    \n    call()')
  assert.deepEqual(enterText(state('\ncall()', 0)), state('\n\ncall()', 1))
})

test('default workshop files include the supplied component tour and outcome experiments', () => {
  const paths = ['main.py', 'ui.py', 'checkpoints/history.py', 'checkpoints/outcome_demo.py']
  assert.deepEqual(new Set(visibleFiles(paths.map(path => ({ path })), false, '').map(file => file.path)), new Set(paths))
})
