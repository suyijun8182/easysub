import test from 'node:test'
import assert from 'node:assert/strict'
import { emptySync, edit, synchronize, resolveConflict } from './engine.js'
import { createTransport, serverUrl } from './transport.js'
const record = (version, name = 'web') => ({ id: 'one', kind: 'categories', version, seq: version, deleted: false, readonly: false, data: { name } })
function fixture() {
  const sync = emptySync(); sync.epoch = 'epoch'
  let records = [record(1)], received = [], loseReply = false
  const receipts = new Map()
  return { sync, received, get records() { return records }, lose() { loseReply = true },
    transport: {
      capabilities: async () => ({ protocol: 1, epoch: 'epoch', max_batch: 100 }),
      changes: async (_, cursor) => ({ epoch: 'epoch', changes: records.filter(r => r.seq > cursor), next_cursor: records.at(-1)?.seq || cursor, has_more: false }),
      push: async ({ operations }) => {
        const results = operations.map(op => {
          received.push(structuredClone(op))
          if (receipts.has(op.op_id)) return receipts.get(op.op_id)
          const next = { ...record((records.at(-1)?.version || 0) + 1), data: op.data, deleted: op.deleted }; records.push(next)
          const result = { op_id: op.op_id, status: 'applied', record: next }; receipts.set(op.op_id, result); return result
        })
        if (loseReply) { loseReply = false; throw new Error('offline') }
        return { epoch: 'epoch', results }
      }
    }
  }
}
test('pull detects simultaneous changes and keeps both until chosen', async () => {
  const f = fixture(); f.sync.records.one = record(0, 'old'); edit(f.sync, 'one', 'categories', { name: 'local' })
  await synchronize(f.sync, f.transport, async () => {})
  assert.equal(f.received.length, 0); assert.equal(f.sync.conflicts.one.local.data.name, 'local'); assert.equal(f.sync.conflicts.one.server.data.name, 'web')
  resolveConflict(f.sync, 'one', 'local'); await synchronize(f.sync, f.transport, async () => {})
  assert.equal(f.received[0].base_version, 1); assert.equal(Object.keys(f.sync.pending).length, 0)
})
test('lost replies replay immutable operation ID after reload', async () => {
  const f = fixture(); await synchronize(f.sync, f.transport, async () => {}); edit(f.sync, 'one', 'categories', { name: 'edited' }); f.lose()
  await assert.rejects(synchronize(f.sync, f.transport, async () => {}), /offline/)
  const saved = structuredClone(f.sync)
  await synchronize(saved, f.transport, async () => {})
  assert.equal(f.received[0].op_id, f.received[1].op_id); assert.equal(f.records.length, 2); assert.equal(Object.keys(saved.pending).length, 0)
})
test('remote deletion requires explicit restore, epoch reset never pushes', async () => {
  const f = fixture(); await synchronize(f.sync, f.transport, async () => {}); edit(f.sync, 'one', 'categories', { name: 'local' })
  f.records.push({ ...record(2), deleted: true }); await synchronize(f.sync, f.transport, async () => {})
  resolveConflict(f.sync, 'one', 'local'); assert.equal(f.sync.pending.one.restore, true)
  f.sync.epoch = 'old'; await assert.rejects(synchronize(f.sync, f.transport, async () => {}), /恢复/); assert.equal(f.received.length, 0)
})
test('URL preserves deployment path and refuses insecure or credentialed servers', () => {
  assert.equal(serverUrl('https://example.com/sub/'), 'https://example.com/sub')
  assert.throws(() => serverUrl('https://user:password@example.com'))
  assert.throws(() => serverUrl('http://192.168.1.5'))
})
test('registration code and OTP remain distinct from bad passwords', async () => {
  const transport = createTransport('https://example.com/sub', {}, async url => {
    assert.equal(url, 'https://example.com/sub/api/auth/login')
    return { ok: false, status: 401, json: async () => ({ detail: { code: 'ACCOUNT_NOT_REGISTERED', message: '注册' } }) }
  })
  await assert.rejects(transport.login('new', 'password'), e => e.code === 'ACCOUNT_NOT_REGISTERED')
})
test('old servers returning HTML or 404 report a missing sync protocol', async () => {
  for (const response of [
    { ok: true, status: 200, json: async () => { throw new SyntaxError('HTML fallback') } },
    { ok: false, status: 404, json: async () => ({ detail: 'Not Found' }) },
    { ok: true, status: 200, json: async () => ({ protocol: 2 }) }
  ]) {
    const transport = createTransport('https://example.com', { access_token: 'test' }, async () => response)
    await assert.rejects(transport.capabilities(), error => error.code === 'SYNC_PROTOCOL_UNAVAILABLE')
  }
})
