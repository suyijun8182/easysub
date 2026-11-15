import test from 'node:test'
import assert from 'node:assert/strict'
import { setImmediate } from 'node:timers/promises'
import { createDeferredDeletion } from './deferred-deletion.js'
import { createPreviewStore } from './store.js'
import { createLocal } from '../sync/local.js'
import { emptySync } from '../sync/engine.js'

test('undo leaves actual data and the sync queue unchanged; expiry queues one tombstone',async t=>{
 t.mock.timers.enable({apis:['setTimeout']})
 const store=createPreviewStore(),doc={local:structuredClone(store.state),sync:emptySync(),mappings:{},link:{server:'https://example.com'},tokens:{},iconCache:{}}
 let saved
 const local=await createLocal(store,{load:async()=>doc,save:async value=>{saved=structuredClone(value)}},()=>{})
 await local.request('get','/api/subscriptions')
 const before=structuredClone(saved),row=structuredClone(store.state.subscriptions[0])
 const deletion=createDeferredDeletion(id=>local.request('delete','/api/subscriptions/'+id),()=>{})
 deletion.stage([row]);assert.ok(deletion.hiddenIds.has(row.id))
 t.mock.timers.tick(4999);assert.deepEqual(saved,before)
 assert.equal(deletion.undo(row.id),true)
 t.mock.timers.tick(1);await setImmediate()
 assert.deepEqual(saved,before);assert.deepEqual(store.state,before.local)
 deletion.stage([row]);t.mock.timers.tick(5000);await setImmediate()
 assert.ok(!store.state.subscriptions.some(s=>s.id===row.id))
 const ops=Object.values(saved.sync.pending);assert.equal(ops.length,1);assert.equal(ops[0].deleted,true)
 assert.equal(deletion.undo(row.id),false)
 deletion.dispose()
})
test('failed persistence restores visibility and remains explicitly retryable',async t=>{
 t.mock.timers.enable({apis:['setTimeout']})
 let fail=true,calls=0
 const deletion=createDeferredDeletion(async()=>{calls++;if(fail)throw new Error('disk full')},()=>{})
 deletion.stage([{id:3,name:'VPS'}]);deletion.stage([{id:3,name:'VPS'}])
 t.mock.timers.tick(5000);await setImmediate()
 assert.equal(calls,1);assert.equal(deletion.entries[0].status,'failed');assert.ok(!deletion.hiddenIds.has(3))
 fail=false;await deletion.retry(3)
 assert.equal(calls,2);assert.equal(deletion.entries.length,0)
 deletion.dispose()
})
