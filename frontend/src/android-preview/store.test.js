import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createPreviewStore, addCycle, encryptBackup, decryptBackup } from './store.js'

test('month-end and leap-year renewal preserve the two starting modes', async () => {
  assert.equal(addCycle('2024-01-31', 'month', 1), '2024-02-29')
  const store = createPreviewStore('2026-11-01')
  const s = await store.request('post', '/api/subscriptions', { name: 'SIM', amount: 10, next_renewal_date: '2026-11-10' })
  const due = await store.request('post', `/api/subscriptions/${s.id}/renew`, { mode: 'due' })
  assert.equal(due.next_renewal_date, '2026-12-10')
  const today = await store.request('post', `/api/subscriptions/${s.id}/renew`, { mode: 'today' })
  assert.equal(today.next_renewal_date, '2026-12-01')
})

test('complete backup restores notes, risk dates, icon, preferences, manual rate and IDs', async () => {
  const store = createPreviewStore('2026-11-01')
  const cat = await store.request('post', '/api/categories', { name: 'Custom', color: '#ff0000' })
  await store.request('post', '/api/currencies', { code: 'ABC', name: '积分', rate_to_base: 2 })
  await store.request('patch', '/api/me', { monthly_budget: 700, category_order: [cat.id], notify_settings: { digest_enabled: true } })
  await store.request('post', '/api/subscriptions', { name: 'All fields', category_id: cat.id, currency: 'ABC', icon: 'data:image/png;base64,aA==', notes: 'long note', trial_end: '2026-12-01', cancel_by: '2026-11-30', card_last4: '1234', card_expiry: '01/28', created_at: '2020-01-01T00:00:00Z' })
  const backup = store.backup()
  const other = createPreviewStore('2026-11-01')
  other.restore(backup, true)
  const restored = (await other.request('get', '/api/subscriptions')).find(s => s.name === 'All fields')
  assert.equal(restored.notes, 'long note')
  assert.equal(restored.trial_end, '2026-12-01')
  assert.equal(restored.card_last4, '1234')
  assert.equal(restored.created_at, '2020-01-01T00:00:00Z')
  assert.equal(other.state.user.monthly_budget, 700)
  assert.equal(other.state.categories.find(c => c.id === restored.category_id).name, 'Custom')
  assert.equal(other.state.rates.ABC, 2)
  const before = JSON.stringify(other.state)
  assert.throws(() => other.restore({ subscriptions: [{ name: 'bad', amount: -4 }] }, true))
  assert.equal(JSON.stringify(other.state), before)
})

test('encrypted backup roundtrips and wrong password cannot recover data', async () => {
  const data = { subscriptions: [], user: { notify_config: { token: 'secret' } } }
  const encrypted = await encryptBackup(data, 'correct password')
  assert.ok(!JSON.stringify(encrypted).includes('secret'))
  assert.deepEqual(await decryptBackup(encrypted, 'correct password'), data)
  await assert.rejects(decryptBackup(encrypted, 'wrong password'))
})

test('all 14 channel configs exist; preview never claims an actual send', async () => {
  const s = createPreviewStore()
  assert.equal(Object.keys((await s.request('get', '/api/notifications/config')).config).length, 14)
  await assert.rejects(s.request('post', '/api/notifications/test', { channel: 'telegram' }), /预览/)
})

test('all existing personal dashboard/report/calendar/list requests are supported', async () => {
  const s = createPreviewStore('2026-11-01')
  for (const url of ['/api/auth/me', '/api/dashboard', '/api/categories', '/api/payment-methods', '/api/bundles', '/api/currencies', '/api/currencies/rate-table', '/api/icons/library', '/api/reports/insights', '/api/reports/category-detail', '/api/reports/ranking', '/api/reports/one-time', '/api/reports/upcoming', '/api/reports/expired', '/api/reports/recent-payments', '/api/reports/export.csv', '/api/logs', '/api/notifications/logs']) {
    assert.notEqual(await s.request('get', url), undefined, url)
  }
  const icons = await s.request('get', '/api/icons/library')
  assert.equal(icons.length, 356)
  assert.equal(new Set(icons.map(x => x.category)).size, 13)
  assert.ok(icons.every(x => x.icon.startsWith('data:image/') || x.icon.startsWith('/preview-icons/')))
})

test('restore remaps notification references and preserves log history', async () => {
  const s = createPreviewStore('2026-11-01')
  const backup = s.backup()
  backup.subscriptions = [{ ...backup.subscriptions[0], id: 789 }]
  backup.notifications = [{ id: 9000, subscription_id: 789, status: 'failed', sent_at: '2026-11-01T00:00:00Z' }]
  backup.logs = [{ id: 9001, action: 'old', created_at: '2020-01-01T00:00:00Z' }]
  s.restore(backup, true)
  assert.equal(s.state.notifications[0].subscription_id, s.state.subscriptions[0].id)
  assert.equal(new Set(s.state.logs.map(l => l.id)).size, s.state.logs.length)
  assert.equal(s.state.logs[0].created_at, '2020-01-01T00:00:00Z')
})

test('invalid dates are rejected and edit cannot overwrite record identity', async () => {
  const s = createPreviewStore('2026-11-01')
  await assert.rejects(s.request('post', '/api/subscriptions', { name: 'bad date', trial_end: '2026-02-31' }), /日期/)
  const item = (await s.request('get', '/api/subscriptions'))[0]
  const changed = await s.request('put', `/api/subscriptions/${item.id}`, { id: 99999, name: 'Edited', notes: 'kept' })
  assert.equal(changed.id, item.id)
  assert.equal(changed.notes, 'kept')
})

test('delete detaches referenced entities and CSV preserves quoted commas', async () => {
  const s = createPreviewStore()
  await s.request('post', '/api/subscriptions/import-csv', { content: 'name,amount,category\r\n"Comma, Name",12,"Test, Category"' })
  const all = await s.request('get', '/api/subscriptions')
  const item = all.find(x => x.name === 'Comma, Name')
  assert.ok(item)
  await s.request('delete', `/api/categories/${item.category_id}`)
  assert.equal((await s.request('get', '/api/subscriptions')).find(x => x.id === item.id).category_id, null)
  assert.match(await s.request('get', '/api/subscriptions/export.csv'), /"Comma, Name"/)
})

test('legacy nullable family members restore without rejecting valid website backup', () => {
  const s = createPreviewStore()
  s.restore({ subscriptions: [{ name: 'Legacy', family_members: null }] }, true)
  assert.deepEqual(s.state.subscriptions[0].family_members, [])
})

test('missing baseline does not report a false zero; manual rate can be set on existing currency', async () => {
  const s = createPreviewStore()
  await s.request('patch', '/api/me', { base_currency: 'JPY' })
  assert.equal((await s.request('get', '/api/reports/insights')).monthly_total, null)
  await s.request('post', '/api/currencies', { code: 'JPY', name: '日元', rate_to_base: 20 })
  assert.ok((await s.request('get', '/api/reports/insights')).monthly_total > 0)
})
