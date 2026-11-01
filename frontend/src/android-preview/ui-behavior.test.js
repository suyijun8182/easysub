import test from 'node:test'
import assert from 'node:assert/strict'
import { appearance, detailBackTarget } from './ui-behavior.js'
import { createPreviewStore } from './store.js'
import { createLocal } from '../sync/local.js'
import { validateConnection } from '../sync/validation.js'
import { syncCopy } from '../sync/copy.js'

test('persisted local preferences survive restarting the app', async () => {
  let saved
  const storage = { load: async () => saved && structuredClone(saved), save: async value => { saved = structuredClone(value) } }
  const store = createPreviewStore(), local = await createLocal(store, storage, () => {})
  await local.request('patch', '/api/me', { theme: 'dark', locale: 'ru' })
  const restarted = createPreviewStore()
  await createLocal(restarted, storage, () => {})
  assert.deepEqual(appearance(restarted.state.user), { theme: 'dark', locale: 'ru' })
  assert.deepEqual(appearance({ theme: 'auto', locale: 'en' }), { theme: 'auto', locale: 'en' })
  assert.deepEqual(appearance({ theme: 'invalid', locale: 'unknown' }), { theme: 'light', locale: 'zh' })
})
test('details opened without app history return to subscriptions, never an external page', () => {
  for (const state of [null, {}, { back: 'https://example.com' }, { back: '//example.com' }, { back: '/subscriptions/1' }]) assert.equal(detailBackTarget(state), '/subscriptions')
  assert.equal(detailBackTarget({ back: '/calendar?month=2026-11' }), '/calendar?month=2026-11')
})
test('connection validation identifies each invalid field without transmitting credentials', () => {
  const t = key => key
  assert.deepEqual(Object.keys(validateConnection({ server: 'http://remote.example', username: ' ', password: '', otp: 'abc' }, t)), ['server', 'username', 'password', 'otp'])
  assert.deepEqual(validateConnection({ server: 'https://sub.example.com/app', username: 'alice', password: 'valid', otp: '123456' }, t), {})
})
test('sync translations are complete, preserve interpolation values and resolve without Chinese UI fallback', () => {
  const placeholders = text => [...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]).sort()
  for (const language of ['en', 'ru']) {
    assert.deepEqual(Object.keys(syncCopy[language]), Object.keys(syncCopy.zh))
    for (const key of Object.keys(syncCopy.zh)) {
      assert.ok(syncCopy[language][key]?.trim())
      assert.deepEqual(placeholders(syncCopy[language][key]), placeholders(syncCopy.zh[key]), key)
      assert.ok(!/[\u4e00-\u9fff]/.test(syncCopy[language][key]), key)
    }
  }
})
