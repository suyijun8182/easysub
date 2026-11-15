import test from 'node:test'
import assert from 'node:assert/strict'
import { upcomingRenewals, recordRenewals } from './renewal-desk.js'
import { createPreviewStore } from './store.js'

test('renewal horizon includes overdue and its boundary, excluding inactive and one-time records', () => {
  const row = (id, date, extra = {}) => ({ id, next_renewal_date: date, is_active: true, billing_type: 'recurring', ...extra })
  const rows = [row(1, '2026-10-31'), row(2, '2026-11-08'), row(3, '2026-11-09'), row(4, '2026-11-02', { is_active: false }), row(5, '2026-11-02', { billing_type: 'one_time' }), row(6, null)]
  assert.deepEqual(upcomingRenewals(rows, 7, new Date(2026, 10, 1)).map(s => s.id), [1, 2])
  assert.equal(rows[0].id, 1)
})

test('partial renewal retry only submits failed IDs and never duplicates a selected ID', async () => {
  const calls = []
  const result = await recordRenewals([1, 1, 2, 3], 'due', async (url, body) => { calls.push([url, body.mode]); if (url.includes('/2/')) throw new Error('offline') })
  assert.deepEqual(result, { applied: [1, 3], failed: [2] })
  const retried = []
  await recordRenewals(result.failed, 'due', async url => retried.push(url))
  assert.equal(calls.length, 3)
  assert.deepEqual(retried, ['/api/subscriptions/2/renew'])
  await assert.rejects(recordRenewals([1], 'unknown', () => { throw new Error('should not submit') }), /Invalid renewal mode/)
})

test('desk renewal uses the existing local API and preserves the chosen due-date mode', async () => {
  const store = createPreviewStore('2026-11-01')
  const sub = await store.request('post', '/api/subscriptions', { name: 'Desk integration', cycle: 'month', cycle_count: 1, start_date: '2026-01-01', next_renewal_date: '2026-12-15' })
  const result = await recordRenewals([sub.id], 'due', (url, data) => store.request('post', url, data))
  assert.deepEqual(result.failed, [])
  assert.equal(store.state.subscriptions.find(s => s.id === sub.id).next_renewal_date, '2027-01-15')
})
