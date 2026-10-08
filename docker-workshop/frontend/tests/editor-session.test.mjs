import assert from 'node:assert/strict'
import { test } from 'node:test'
import { EditorSession } from '../src/editorSession.ts'

const document = (path, content) => ({ path, content, language: 'python' })

test('opens nested files and persists their edited contents', async () => {
  const files = new Map([['checkpoints/chat.py', 'print(1)']])
  const session = new EditorSession({
    read: async path => document(path, files.get(path)),
    write: async (path, content) => { files.set(path, content) }
  })
  assert.equal(await session.open('checkpoints/chat.py'), true)
  session.content = 'print(2)'
  assert.equal(session.dirty, true)
  assert.equal(await session.save(), true)
  assert.equal(files.get('checkpoints/chat.py'), 'print(2)')
  assert.equal(session.dirty, false)
})

test('a failed save preserves edits and prevents switching files', async () => {
  const session = new EditorSession({
    read: async path => document(path, 'original'),
    write: async () => { throw new Error('Disk is full') }
  })
  await session.open('agent.py')
  session.content = 'my solution'
  assert.equal(await session.open('tools.py'), false)
  assert.equal(session.path, 'agent.py')
  assert.equal(session.content, 'my solution')
  assert.equal(session.dirty, true)
  assert.match(session.error, /Disk is full/)
})

test('typing during a save does not mark unsaved text as persisted', async () => {
  let finish
  const session = new EditorSession({
    read: async path => document(path, 'original'),
    write: () => new Promise(resolve => { finish = resolve })
  })
  await session.open('agent.py')
  session.content = 'first edit'
  const pending = session.save()
  session.content = 'second edit'
  finish()
  assert.equal(await pending, true)
  assert.equal(session.dirty, true)
  assert.equal(session.content, 'second edit')
})

test('a failed read leaves the current file intact', async () => {
  const session = new EditorSession({
    read: async path => {
      if (path === 'missing.py') throw new Error('File not found')
      return document(path, 'original')
    },
    write: async () => {}
  })
  await session.open('agent.py')
  assert.equal(await session.open('missing.py'), false)
  assert.equal(session.path, 'agent.py')
  assert.equal(session.content, 'original')
  assert.match(session.error, /File not found/)
})

function deferred() {
  let resolve, reject
  const promise = new Promise((yes, no) => { resolve = yes; reject = no })
  return { promise, resolve, reject }
}

const tick = () => new Promise(resolve => setImmediate(resolve))

test('the latest requested file wins during the initial read', async () => {
  const first = deferred()
  const reads = []
  const session = new EditorSession({
    read: async path => { reads.push(path); return path === 'first_call.py' ? first.promise : document(path, path) },
    write: async () => {}
  })
  const initial = session.open('first_call.py')
  await tick()
  const middle = session.open('tools.py')
  const latest = session.open('agent.py')
  first.resolve(document('first_call.py', 'old lesson'))
  await Promise.all([initial, middle, latest])
  assert.equal(session.path, 'agent.py')
  assert.equal(session.content, 'agent.py')
  assert.deepEqual(reads, ['first_call.py', 'agent.py'])
})

test('a file request waits for an in-flight save', async () => {
  const save = deferred()
  const session = new EditorSession({
    read: async path => document(path, 'original'),
    write: () => save.promise
  })
  await session.open('agent.py')
  session.content = 'solution'
  const saving = session.save()
  const opening = session.open('tools.py')
  save.resolve()
  await Promise.all([saving, opening])
  assert.equal(session.path, 'tools.py')
})

test('queued requests cannot discard edits after an in-flight save fails', async () => {
  const save = deferred()
  const session = new EditorSession({
    read: async path => document(path, 'original'),
    write: () => save.promise
  })
  await session.open('agent.py')
  session.content = 'solution'
  const saving = session.save()
  const opening = session.open('tools.py')
  save.reject(new Error('Offline'))
  await Promise.all([saving, opening])
  assert.equal(session.path, 'agent.py')
  assert.equal(session.content, 'solution')
  assert.equal(session.dirty, true)
  assert.equal(session.error, 'Offline')
})

test('edits typed during a queued switch are preserved', async () => {
  const save = deferred()
  const session = new EditorSession({
    read: async path => document(path, 'original'),
    write: () => save.promise
  })
  await session.open('agent.py')
  session.content = 'first edit'
  const opening = session.open('tools.py')
  await tick()
  session.content = 'newer edit'
  save.resolve()
  assert.equal(await opening, false)
  assert.equal(session.path, 'agent.py')
  assert.equal(session.content, 'newer edit')
})

test('reload reads external changes without switching files', async () => {
  let content = 'before'
  const session = new EditorSession({ read: async path => document(path, content), write: async () => {} })
  await session.open('tools.py')
  content = 'edited in terminal'
  assert.equal(await session.reload(), true)
  assert.equal(session.content, content)
  assert.equal(session.dirty, false)
})

test('reload refuses to discard local pending edits', async () => {
  let reads = 0
  const session = new EditorSession({ read: async path => { reads++; return document(path, 'original') }, write: async () => {} })
  await session.open('tools.py')
  session.content = 'unsaved solution'
  assert.equal(await session.reload(), false)
  assert.equal(reads, 1)
  assert.equal(session.content, 'unsaved solution')
  assert.match(session.error, /save.*reload/i)
})
