import test from 'node:test'
import assert from 'node:assert/strict'
import { createLocal } from './local.js'
import { createPreviewStore } from '../android-preview/store.js'
import { createTransport } from './transport.js'
test('real FastAPI HTTP: local creation reaches website and web edits return with all fields', { skip: process.env.EASYSUB_SYNC_FIXTURE !== '1' }, async () => {
  const server = 'http://127.0.0.1:18765'
  let saved
  const store = createPreviewStore(), local = await createLocal(store, { load: async () => null, save: async value => { saved = structuredClone(value) } }, () => {})
  const category = await local.request('post', '/api/categories', { name: 'HTTP category', color: '#123456' })
  const name = 'Local HTTP ' + crypto.randomUUID()
  const created = await local.request('post', '/api/subscriptions', { name, amount: 45, notes: 'complete notes', trial_end: '2026-12-10', cancel_by: '2026-12-09', card_last4: '1234', card_expiry: '12/28', category_id: category.id })
  const candidate = await local.test(server, 'sync-fixture', 'fixture-password')
  await local.connect(candidate)
  assert.equal(Object.keys(local.status.conflicts).length, 0, JSON.stringify(local.status.conflicts))
  const transport = createTransport(server, saved.tokens)
  const website = await transport.request('/api/subscriptions')
  const row = website.find(s => s.name === name)
  assert.ok(row); assert.equal(row.card_last4, '1234'); assert.equal(row.trial_end, '2026-12-10')
  await transport.request('/api/subscriptions/' + row.id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'Edited on website', notes: 'web notes', card_expiry: '11/29' }) })
  await local.sync()
  const localRow = store.state.subscriptions.find(s => s.id === created.id)
  assert.equal(localRow.name, 'Edited on website')
  assert.equal(localRow.card_expiry, '11/29')
  assert.equal(localRow.notes, 'web notes')
  await local.request('put', '/api/subscriptions/' + created.id, { name: 'Offline conflict retained' })
  await transport.request('/api/subscriptions/' + row.id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'Concurrent web version' }) })
  await local.sync()
  const conflict = Object.values(local.status.conflicts)[0]
  assert.equal(conflict.local.data.name, 'Offline conflict retained')
  assert.equal(conflict.server.data.name, 'Concurrent web version')
  assert.equal((await transport.request('/api/subscriptions/' + row.id)).name, 'Concurrent web version')
})
