import assert from 'node:assert/strict'
import { test } from 'node:test'
import { SelfChecks } from '../src/selfChecks.ts'

const steps = [{ file: 'one.md', title: 'One' }, { file: 'two.md', title: 'Two' }]
function memoryStorage() {
  const data = new Map()
  return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value) }
}

test('self-checks start unconfirmed, survive reload, and can be unchecked', () => {
  const storage = memoryStorage()
  const progress = new SelfChecks(() => storage)
  assert.deepEqual(progress.summary(steps).map(step => step.confirmed), [false, false])
  progress.set('one.md', true)
  const reloaded = new SelfChecks(() => storage)
  assert.deepEqual(reloaded.summary(steps).map(step => step.confirmed), [true, false])
  reloaded.set('one.md', false)
  assert.equal(new SelfChecks(() => storage).confirmed('one.md'), false)
})

test('only explicit boolean true counts and stale lesson keys do not inflate the summary', () => {
  const storage = memoryStorage()
  const progress = new SelfChecks(() => storage)
  progress.set('removed.md', true)
  assert.equal(progress.summary(steps).filter(step => step.confirmed).length, 0)
  const legacy = memoryStorage()
  legacy.setItem('coding-agent-build-self-checks-v1', '{"one.md":"true","two.md":true}')
  assert.deepEqual(new SelfChecks(() => legacy).summary(steps).map(step => step.confirmed), [false, true])
})

test('storage failure keeps the current self-check and explains it will not persist', () => {
  const progress = new SelfChecks(() => ({ getItem: () => null, setItem: () => { throw new Error('quota') } }))
  progress.set('one.md', true)
  assert.equal(progress.confirmed('one.md'), true)
  assert.match(progress.error, /lost when you reload/i)
})

test('corrupt or unavailable saved progress does not break lesson navigation', () => {
  for (const storage of [() => { throw new Error('blocked') }, () => ({ getItem: () => '{bad', setItem() {} })]) {
    const progress = new SelfChecks(storage)
    assert.equal(progress.confirmed('one.md'), false)
    assert.ok(progress.error)
  }
})

test('practical, explanation, live attempt and notes persist independently per lesson', () => {
  const storage = memoryStorage()
  const progress = new SelfChecks(() => storage)
  progress.set('one.md', true)
  progress.update('one.md', { explanationCompared: true, notes: 'Expected a read; observed a write.' })
  progress.update('two.md', { liveModelAttempted: true })
  const reloaded = new SelfChecks(() => storage)
  assert.deepEqual(reloaded.evidence('one.md'), { practicalChecked: true, explanationCompared: true, liveModelAttempted: false, notes: 'Expected a read; observed a write.' })
  assert.deepEqual(reloaded.evidence('two.md'), { practicalChecked: false, explanationCompared: false, liveModelAttempted: true, notes: '' })
  reloaded.set('one.md', false)
  assert.equal(reloaded.evidence('one.md').explanationCompared, true)
})

test('legacy boolean evidence migrates practical credit only and never overrides newer records', () => {
  const storage = memoryStorage()
  storage.setItem('coding-agent-build-self-checks-v1', '{"one.md":true,"two.md":"true"}')
  let progress = new SelfChecks(() => storage)
  assert.deepEqual(progress.evidence('one.md'), { practicalChecked: true, explanationCompared: false, liveModelAttempted: false, notes: '' })
  assert.equal(progress.confirmed('two.md'), false)
  progress.set('one.md', false)
  progress = new SelfChecks(() => storage)
  assert.equal(progress.confirmed('one.md'), false)
})

test('invalid current records report an error instead of awarding evidence', () => {
  const storage = memoryStorage()
  storage.setItem(SelfChecks.storageKey, '{"one.md":{"practicalChecked":"true","notes":23}}')
  const progress = new SelfChecks(() => storage)
  assert.equal(progress.confirmed('one.md'), false)
  assert.ok(progress.error)
})
