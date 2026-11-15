import test from 'node:test'
import assert from 'node:assert/strict'
import { createPullRefresh, PULL_THRESHOLD } from './pull-refresh.js'

test('pull refresh never requests the server in local-only mode', async () => {
  let calls = 0
  const pull = createPullRefresh({ status: () => ({ link: null }), sync: async () => { calls++ } })
  assert.equal(await pull.release(PULL_THRESHOLD + 40), 'local')
  assert.equal(await createPullRefresh({ status: () => null, sync: async () => { calls++ } }).release(PULL_THRESHOLD), 'local')
  assert.equal(calls, 0)
})

test('connected pull triggers exactly one sync even when released again mid-flight', async () => {
  let calls = 0, finish
  const pull = createPullRefresh({ status: () => ({ link: { server: 'https://example.com' } }), sync: () => { calls++; return new Promise(resolve => { finish = resolve }) } })
  assert.equal(await pull.release(PULL_THRESHOLD - 1), 'cancel')
  const first = pull.release(PULL_THRESHOLD)
  assert.equal(await pull.release(PULL_THRESHOLD * 2), 'busy')
  finish(); assert.equal(await first, 'synced')
  assert.equal(calls, 1)
})

test('sync failure is reported without throwing out of the gesture', async () => {
  const pull = createPullRefresh({ status: () => ({ link: {} }), sync: async () => { throw new Error('offline') } })
  assert.equal(await pull.release(PULL_THRESHOLD), 'failed')
})
