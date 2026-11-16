import test from 'node:test'
import assert from 'node:assert/strict'
import { createBackgroundCheck } from './background-check.js'
import { renderClass } from './template-test-helper.js'
function fixture({ native = true, fail = false } = {}) {
  const calls = []
  const device = {
    setBackgroundCheck: async value => { calls.push(['set', value]); if (fail) throw new Error('disk') },
    clearBackgroundCheck: async () => { calls.push(['clear']) },
    backgroundCheckStatus: async () => ({ enabled: true }),
    setBackgroundCheckEnabled: async ({ enabled }) => { calls.push(['enabled', enabled]); return { enabled } }
  }
  const state = {}
  const check = createBackgroundCheck({ native: () => native, device, locale: () => 'en', state })
  return { check, calls, state }
}
const snapshot = (cursor = 198) => ({ server: 'https://sync.example.com', tokens: { access_token: 'a', refresh_token: 'r' }, epoch: 'e1', cursor })
test('a sync snapshot is handed to the device once per distinct value', async () => {
  const f = fixture()
  await f.check.synced(snapshot()); await f.check.synced(snapshot()); await f.check.synced(snapshot(199))
  assert.deepEqual(f.calls, [
    ['set', { server: 'https://sync.example.com', access_token: 'a', refresh_token: 'r', epoch: 'e1', cursor: 198, locale: 'en' }],
    ['set', { server: 'https://sync.example.com', access_token: 'a', refresh_token: 'r', epoch: 'e1', cursor: 199, locale: 'en' }]
  ])
})
test('unlinking clears the device snapshot and forgets the last value', async () => {
  const f = fixture()
  await f.check.synced(snapshot()); await f.check.unlinked(); await f.check.synced(snapshot())
  assert.deepEqual(f.calls.map(c => c[0]), ['set', 'clear', 'set'])
})
test('a failed handoff is retried on the next sync and never throws into the sync engine', async () => {
  const f = fixture({ fail: true })
  await f.check.synced(snapshot()); await f.check.synced(snapshot())
  assert.equal(f.calls.length, 2)
})
test('browser preview never calls the device', async () => {
  const f = fixture({ native: false })
  await f.check.synced(snapshot()); await f.check.unlinked(); await f.check.refresh(); await f.check.setEnabled(false)
  assert.deepEqual(f.calls, []); assert.equal(f.state.available, false)
})
test('toggle state follows the device', async () => {
  const f = fixture()
  await f.check.refresh(); assert.equal(f.state.enabled, true); assert.equal(f.state.available, true)
  await f.check.setEnabled(false); assert.equal(f.state.enabled, false); assert.deepEqual(f.calls.at(-1), ['enabled', false])
})
test('toggle explains what is sent and is only interactive on the device', async () => {
  const t = key => key
  for (const [available, disabled] of [[true, false], [false, true]]) {
    const html = await renderClass('./BackgroundCheckToggle.vue', 'background-check', { check: { state: { enabled: true, available, busy: false, error: false } }, t })
    assert.match(html, /sync.backgroundHint/); assert.equal(/<input[^>]+disabled/.test(html), disabled)
  }
})
