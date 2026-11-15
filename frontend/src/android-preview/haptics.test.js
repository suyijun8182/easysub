import test from 'node:test'
import assert from 'node:assert/strict'
import { createHaptics, hapticsEnabled, setHapticsEnabled } from './haptics.js'

function fakePlugin(calls) {
  return async () => ({
    ImpactStyle: { Light: 'LIGHT', Medium: 'MEDIUM' }, NotificationType: { Success: 'SUCCESS' },
    Haptics: { impact: async o => calls.push(['impact', o.style]), notification: async o => calls.push(['notification', o.type]) }
  })
}

test('browser preview skips haptics without loading the plugin', async () => {
  let loaded = 0
  const h = createHaptics({ native: () => false, enabled: () => true, load: async () => { loaded++ } })
  assert.equal(await h.tick(), false); assert.equal(await h.success(), false); assert.equal(await h.warning(), false)
  assert.equal(loaded, 0)
})

test('native haptics fire the three agreed patterns and respect the switch', async () => {
  const calls = []; let on = true
  const h = createHaptics({ native: () => true, enabled: () => on, load: fakePlugin(calls) })
  await h.tick(); await h.success(); await h.warning()
  assert.deepEqual(calls, [['impact', 'LIGHT'], ['notification', 'SUCCESS'], ['impact', 'MEDIUM']])
  on = false; assert.equal(await h.tick(), false); assert.equal(calls.length, 3)
})

test('plugin failures never escape to the UI', async () => {
  const h = createHaptics({ native: () => true, enabled: () => true, load: async () => { throw new Error('missing plugin') } })
  assert.equal(await h.success(), false)
})

test('switch defaults on and persists independently of reduced motion', () => {
  const data = new Map()
  globalThis.localStorage = { getItem: k => data.get(k) ?? null, setItem: (k, v) => data.set(k, v) }
  assert.equal(hapticsEnabled(), true)
  setHapticsEnabled(false); assert.equal(hapticsEnabled(), false)
  setHapticsEnabled(true); assert.equal(hapticsEnabled(), true)
  delete globalThis.localStorage
})
