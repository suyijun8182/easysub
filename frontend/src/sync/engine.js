export const emptySync = () => ({ device_id: crypto.randomUUID(), epoch: null, cursor: 0, records: {}, pending: {}, conflicts: {}, enabled: false, last_success: null })
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b)
export function edit(sync, id, kind, data, deleted = false) {
  const old = sync.pending[id], server = sync.records[id]
  if (server?.readonly) throw new Error('系统项目不能修改')
  sync.pending[id] = { op_id: crypto.randomUUID(), id, kind, data: structuredClone(data), deleted, base_version: server?.version || 0 }
  if (old?.restore) sync.pending[id].restore = true
  if (sync.conflicts[id]) sync.conflicts[id].local = structuredClone(sync.pending[id])
  // A changed in-flight request remains intact until its receipt arrives.
}
function receive(sync, record) {
  if (!record || (sync.records[record.id]?.version || 0) >= record.version) return
  const local = sync.pending[record.id]
  sync.records[record.id] = record
  if (local && (local.deleted !== record.deleted || !same(local.data, record.data))) sync.conflicts[record.id] = { local: structuredClone(local), server: record }
}
export function resolveConflict(sync, id, choice) {
  const conflict = sync.conflicts[id]
  if (!conflict) return
  if (choice === 'server') delete sync.pending[id]
  else {
    const local = sync.pending[id] || conflict.local
    sync.pending[id] = { ...local, op_id: crypto.randomUUID(), base_version: conflict.server?.version || 0, restore: !!conflict.server?.deleted && !local.deleted }
  }
  delete sync.conflicts[id]
}
export async function synchronize(sync, transport, persist) {
  // Persist each immutable batch before sending; lost replies replay the same operation IDs.
  const caps = await transport.capabilities()
  if (caps.protocol !== 1) throw new Error('服务器尚不支持同步协议 v1')
  if (caps.epoch !== sync.epoch) throw Object.assign(new Error('服务器资料库已恢复，请重新审核合并；本地数据已保留'), { code: 'RESET_REQUIRED' })
  if (sync.inflight?.length) await send(sync.inflight)
  let page
  do {
    page = await transport.changes(sync.epoch, sync.cursor)
    if (page.epoch !== sync.epoch || page.next_cursor < sync.cursor) throw new Error('服务器同步游标无效')
    for (const record of page.changes) receive(sync, record)
    sync.cursor = page.next_cursor
    await persist()
  } while (page.has_more)
  const operations = Object.values(sync.pending).filter(op => !sync.conflicts[op.id])
  for (let i = 0; i < operations.length; i += caps.max_batch || 100) {
    sync.inflight = structuredClone(operations.slice(i, i + (caps.max_batch || 100)))
    await persist(); await send(sync.inflight)
  }
  sync.last_success = new Date().toISOString(); await persist()
  async function send(batch) {
    const response = await transport.push({ epoch: sync.epoch, device_id: sync.device_id, operations: batch })
    if (response.epoch !== sync.epoch || !Array.isArray(response.results) || response.results.length !== batch.length) throw new Error('服务器同步响应不完整，本地队列已保留')
    for (const operation of batch) {
      const result = response.results.find(r => r.op_id === operation.op_id)
      if (!result) throw new Error('服务器缺少操作回执')
      if (result.status === 'applied') {
        if (result.record) sync.records[operation.id] = result.record
        if (sync.pending[operation.id]?.op_id === operation.op_id) { delete sync.pending[operation.id]; delete sync.conflicts[operation.id] }
        else if (sync.pending[operation.id]) sync.pending[operation.id].base_version = result.record?.version || 0
      } else sync.conflicts[operation.id] = { local: sync.pending[operation.id] || operation, server: result.server || sync.records[operation.id] || null, error: result.message || result.code }
    }
    sync.inflight = null; await persist()
  }
}
