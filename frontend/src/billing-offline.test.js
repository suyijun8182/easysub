import test from 'node:test'
import assert from 'node:assert/strict'
import { createPreviewStore } from './android-preview/store.js'

test('离线续费与完整表单编辑保留月末锚定日', async () => {
  const store = createPreviewStore('2027-01-01')
  let s = await store.request('post', '/api/subscriptions', {name: '月末', start_date: '2027-01-31', next_renewal_date: '2027-01-31'})
  s = await store.request('post', `/api/subscriptions/${s.id}/renew`, {mode: 'due'})
  assert.equal(s.next_renewal_date, '2027-02-28')
  s = await store.request('put', `/api/subscriptions/${s.id}`, {...s, remark: '备注', billing_anchor_day: 28})
  assert.equal(s.billing_anchor_day, 31)
  s = await store.request('post', `/api/subscriptions/${s.id}/renew`, {mode: 'due'})
  assert.equal(s.next_renewal_date, '2027-03-31')
})

test('离线 CSV 往返保留短月前的锚定日', async () => {
  const store = createPreviewStore('2027-01-01')
  const s = await store.request('post', '/api/subscriptions', {name: '月末CSV', start_date: '2027-01-31', next_renewal_date: '2027-02-28', billing_anchor_day: 31})
  const content = await store.request('get', '/api/subscriptions/export.csv')
  assert.ok(content.includes('billing_anchor_day'))
  const imported = createPreviewStore('2027-01-01')
  await imported.request('post', '/api/subscriptions/import-csv', {content})
  const items = await imported.request('get', '/api/subscriptions')
  const row = items.find(x => x.name === s.name)
  assert.equal(row.billing_anchor_day, 31)
  const renewed = await imported.request('post', `/api/subscriptions/${row.id}/renew`, {mode: 'due'})
  assert.equal(renewed.next_renewal_date, '2027-03-31')
})
