import test from 'node:test'
import assert from 'node:assert/strict'
import { createLocal } from './local.js'
import { createPreviewStore } from '../android-preview/store.js'
function fixture(extra = []) {
  let saved, seq = 0
  const records = {}, changes = [], receipts = new Map()
  const add = (kind, data, readonly = false) => { const row = { id: crypto.randomUUID(), kind, data, readonly, version: 1, seq: ++seq, deleted: false }; records[row.id] = row; changes.push(structuredClone(row)); return row }
  add('categories', { name: '视频', icon: '🎬', is_system: true, sort: 0 }, true)
  add('currencies', { code: 'CNY', name: '人民币', symbol: '¥', is_custom: false, rate_base: 'CNY', rate_to_base: 1 }, true)
  add('preferences', { base_currency: 'CNY', monthly_budget: 100, category_order: [], notify_settings: {} })
  add('notification-config', {})
  for (const item of extra) add(item.kind, item.data)
  const caps = { protocol: 1, epoch: crypto.randomUUID(), account_id: 1, username: 'alice', exchange_base: 'CNY', max_batch: 100 }
  let offline = false
  const transport = {
    login: async () => ({ access_token: 'access', refresh_token: 'refresh' }),
    capabilities: async () => { if (offline) throw new Error('offline'); return caps },
    changes: async (_, cursor) => ({ epoch: caps.epoch, changes: structuredClone(changes.filter(r => r.seq > cursor)), next_cursor: seq, has_more: false }),
    push: async ({ operations }) => ({ epoch: caps.epoch, results: operations.map(op => {
      if (receipts.has(op.op_id)) return receipts.get(op.op_id)
      const record = { id: op.id, kind: op.kind, data: structuredClone(op.data), version: (records[op.id]?.version || 0) + 1, seq: ++seq, deleted: op.deleted, readonly: false }
      records[op.id] = record; changes.push(structuredClone(record)); const result = { op_id: op.op_id, status: 'applied', record }; receipts.set(op.op_id, result); return result
    }) })
  }
  return { storage: { load: async () => saved && structuredClone(saved), save: async value => { saved = structuredClone(value) } }, transport: () => transport, candidate: { server: 'https://example.com', username: 'alice', account_id: 1, tokens: {}, caps }, records, add, offline(value) { offline = value }, get saved() { return saved } }
}
test('real local entry starts empty, merges full local entities, survives reload and uploads offline edits', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  assert.equal(store.state.subscriptions.length, 0)
  const category = await local.request('post', '/api/categories', { name: 'Personal', color: '#123456' })
  const sub = await local.request('post', '/api/subscriptions', { name: 'Mine', category_id: category.id, notes: 'kept', card_last4: '1234', trial_end: '2026-12-01' })
  await local.connect(f.candidate)
  const remote = Object.values(f.records).find(r => r.kind === 'subscriptions')
  assert.equal(f.records[remote.data.category_id].data.name, 'Personal'); assert.equal(remote.data.card_last4, '1234')
  f.offline(true)
  await local.request('put', '/api/subscriptions/' + sub.id, { name: 'Offline edited' })
  await assert.rejects(local.sync(), /offline/)
  const reloadedStore = createPreviewStore(), reloaded = await createLocal(reloadedStore, f.storage, () => {}, f.transport)
  assert.equal(reloadedStore.state.subscriptions[0].name, 'Offline edited')
  f.offline(false); await reloaded.sync()
  assert.equal(Object.values(f.records).find(r => r.kind === 'subscriptions').data.name, 'Offline edited')
  assert.equal(Object.keys(reloaded.status.pending).length, 0)
})
test('website backup custom currency and manual rate survive first sync and restart', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.restore({ subscriptions: [{ name: 'Custom currency sub', amount: 10, currency: 'ABC' }], currencies: [{ code: 'ABC', name: 'Custom', symbol: 'A' }], rates: { CNY: 1, ABC: 3 }, rate_base: 'CNY' })
  await local.connect(f.candidate)
  assert.equal(store.state.currencies.find(c => c.code === 'ABC')?.name, 'Custom')
  assert.equal(store.state.rates.ABC, 3)
  assert.ok(Object.values(f.records).some(r => r.kind === 'currencies' && r.data.code === 'ABC' && r.data.rate_to_base === 3))
  const reloaded = createPreviewStore()
  await createLocal(reloaded, f.storage, () => {}, f.transport)
  assert.equal(reloaded.state.currencies.find(c => c.code === 'ABC')?.symbol, 'A')
  assert.equal(reloaded.state.rates.ABC, 3)
})

test('first connection copies reactive credentials into serializable local state', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  const tokens = new Proxy({ access_token: 'access', refresh_token: 'refresh' }, {})
  const candidate = new Proxy({ ...f.candidate, tokens }, {})
  await local.connect(candidate)
  assert.equal(local.status.link.username, 'alice')
  assert.equal(local.status.enabled, true)
  assert.equal(Object.keys(local.status.pending).length, 0)
  assert.equal(f.saved.tokens.access_token, 'access')
})
test('initial currency code collision leaves local data and mapping untouched', async () => {
  const f = fixture([{ kind: 'currencies', data: { code: 'ABC', name: 'server', is_custom: true, rate_to_base: 2 } }])
  const store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.request('post', '/api/currencies', { code: 'ABC', name: 'local', symbol: 'A', rate_to_base: 3 })
  await assert.rejects(local.connect(f.candidate), /代码重复/)
  assert.equal(local.status.link, null); assert.equal(store.state.currencies.filter(r => r.code === 'ABC').length, 1)
  assert.equal(store.state.currencies.find(r => r.code === 'ABC').name, 'local')
})
test('other-account connection never uploads the previous account data', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.connect(f.candidate)
  await assert.rejects(local.connect({ ...f.candidate, account_id: 2 }), /另一服务器或账号/)
  assert.equal(local.status.link.account_id, 1)
  await local.logout(); assert.deepEqual(f.saved.tokens, {}); assert.equal(local.status.enabled, false)
})
test('incremental currency collision preserves mapping, edits and both versions', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.connect(f.candidate)
  await local.request('post', '/api/currencies', { code: 'ABC', name: 'local', symbol: 'A', rate_to_base: 3 })
  const localId = f.saved.mappings['currencies:ABC']
  f.add('currencies', { code: 'ABC', name: 'web', symbol: 'B', is_custom: true, rate_base: 'CNY', rate_to_base: 4 })
  await local.sync()
  assert.equal(store.state.currencies.filter(r => r.code === 'ABC').length, 1)
  assert.equal(f.saved.mappings['currencies:ABC'], localId)
  assert.equal(local.status.conflicts[localId].local.data.name, 'local')
  assert.equal(local.status.conflicts[localId].server.data.name, 'web')
  await local.request('put', '/api/currencies/ABC', { name: 'local still editable' })
  assert.equal(local.status.pending[localId].data.name, 'local still editable')
  await assert.rejects(local.resolve(localId, 'local'), /两个相同币种代码/)
  await local.resolve(localId, 'server')
  assert.equal(store.state.currencies.filter(r => r.code === 'ABC').length, 1)
  assert.equal(store.state.currencies.find(r => r.code === 'ABC').name, 'web')
})
test('local writes interrupt a stalled network sync and still persist', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.connect(f.candidate)
  let rejectRequest, started
  const waiting = new Promise(resolve => { started = resolve })
  const transport = f.transport()
  transport.capabilities = () => new Promise((_, reject) => { rejectRequest = reject; started() })
  transport.abort = () => rejectRequest(Object.assign(new Error('cancelled for local use'), { name: 'AbortError' }))
  const syncing = local.sync(); await waiting
  await local.request('post', '/api/subscriptions', { name: 'Works offline immediately' })
  await syncing
  assert.equal(f.saved.local.subscriptions[0].name, 'Works offline immediately')
  assert.equal(Object.keys(f.saved.sync.pending).length, 1)
})
test('server losing sync support pauses automatic sync without losing pending edits', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.connect(f.candidate)
  await local.request('post', '/api/subscriptions', { name: 'Preserve pending' })
  f.transport().capabilities = async () => { throw Object.assign(new Error('upgrade needed'), { code: 'SYNC_PROTOCOL_UNAVAILABLE' }) }
  await assert.rejects(local.sync(), /upgrade needed/)
  assert.equal(local.status.enabled, false)
  assert.equal(Object.keys(local.status.pending).length, 1)
  assert.equal(store.state.subscriptions[0].name, 'Preserve pending')
})
test('first connection preserves offline preferences and notification secrets as explicit conflicts', async () => {
  const f = fixture(), store = createPreviewStore(), local = await createLocal(store, f.storage, () => {}, f.transport)
  await local.request('patch', '/api/me', { monthly_budget: 700 })
  const config = structuredClone(store.state.config)
  config.telegram = { ...config.telegram, enabled: true, bot_token: 'local-fixture-secret' }
  await local.request('put', '/api/notifications/config', { config })
  const restartedStore = createPreviewStore(), restarted = await createLocal(restartedStore, f.storage, () => {}, f.transport)
  await restarted.connect(f.candidate)
  assert.equal(restartedStore.state.user.monthly_budget, 700)
  assert.equal(restartedStore.state.config.telegram.bot_token, 'local-fixture-secret')
  assert.equal(Object.keys(restarted.status.conflicts).length, 2)
  const preferences = Object.values(f.records).find(record => record.kind === 'preferences')
  assert.equal(preferences.data.monthly_budget, 100)
  await restarted.resolve(preferences.id, 'local')
  assert.equal(f.records[preferences.id].data.monthly_budget, 700)
  const notification = Object.values(f.records).find(record => record.kind === 'notification-config')
  assert.deepEqual(notification.data, {})
})
