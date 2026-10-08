import assert from 'node:assert/strict'
import { test } from 'node:test'
import { getBasePath, getApiUrl } from '../src/utils/basePath.js'

test('direct guide routes resolve content beneath /guide and API calls at the workbench root', () => {
  globalThis.window = { location: { pathname: '/guide/build' } }
  assert.equal(getBasePath(), '/guide')
  assert.equal(getApiUrl('/api/editor/files'), '/api/editor/files')
  window.location.pathname = '/guide'
  assert.equal(getBasePath(), '/guide')
})

test('compiled guide base and standalone proxy routes both retain their asset and API routing', () => {
  const previous = process.env.BASE_URL
  try {
    process.env.BASE_URL = '/guide/'
    globalThis.window = { location: { pathname: '/' } }
    assert.equal(getBasePath(), '/guide')
    assert.equal(getApiUrl('/api/editor/files'), '/api/editor/files')
    process.env.BASE_URL = '/'
    window.location.pathname = '/hub/workshop/agent/build'
    assert.equal(getBasePath(), '/hub/workshop/agent')
    assert.equal(getApiUrl('/api/editor/files'), '/hub/workshop/agent/api/editor/files')
  } finally {
    if (previous === undefined) delete process.env.BASE_URL
    else process.env.BASE_URL = previous
  }
})
