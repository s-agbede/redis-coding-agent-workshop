import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import { getEnabledPhases, getNextPhase, loadWorkshopConfig } from '../src/utils/workshopConfig.js'

test('the shipped configuration starts with the workshop immediately after welcome', async () => {
  globalThis.window = { location: { pathname: '/guide/' } }
  const yaml = await readFile(new URL('../public/workshop.config.yaml', import.meta.url), 'utf8')
  globalThis.fetch = async () => ({ ok: true, text: async () => yaml })
  const config = await loadWorkshopConfig()
  assert.deepEqual(getEnabledPhases(config).map(phase => phase.route), ['/', '/build'])
  assert.equal(getNextPhase(config, 'welcome').route, '/build')
  assert.equal(getNextPhase(config, 'build'), null)
})

test('navigation still opens the workshop when configuration is unavailable', () => {
  assert.deepEqual(getEnabledPhases(null).map(phase => phase.route), ['/', '/build'])
  assert.equal(getNextPhase(null, 'welcome').route, '/build')
})
