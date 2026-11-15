export const DELETE_UNDO_MS = 5000
// Defer the actual local write, so undo never needs a compensating sync record.
export function createDeferredDeletion(remove, changed) {
  const pending=new Map(), committed=new Set()
  async function commit(id) {
    const item=pending.get(id)
    if (!item || item.status==='saving') return
    item.status='saving';changed()
    try { await remove(id);committed.add(id);pending.delete(id) }
    catch(error){item.status='failed';item.error=error.message}
    changed()
  }
  return {
    get entries(){return [...pending.values()]},
    get hiddenIds(){return new Set([...committed,...[...pending.values()].filter(e=>e.status!=='failed').map(e=>e.row.id)])},
    stage(rows){for(const row of rows){if(pending.has(row.id)||committed.has(row.id))continue;const item={row:{id:row.id,name:row.name},status:'pending'};item.timer=setTimeout(()=>commit(row.id),DELETE_UNDO_MS);pending.set(row.id,item)}changed()},
    undo(id){const item=pending.get(id);if(item?.status!=='pending')return false;clearTimeout(item.timer);pending.delete(id);changed();return true},
    retry:commit,
    dispose(){for(const item of pending.values())clearTimeout(item.timer);pending.clear()}
  }
}
