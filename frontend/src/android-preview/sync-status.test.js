import test from 'node:test'
import assert from 'node:assert/strict'
import { syncStatus, showRawSyncError } from './sync-status.js'
import { createPreviewStore } from './store.js'
import { createLocal } from '../sync/local.js'
import { emptySync } from '../sync/engine.js'
test('sync state never treats login as completed synchronization',()=>{
  assert.equal(syncStatus(null),'local')
  const connected={link:{},enabled:true,pending:{},conflicts:{}}
  assert.equal(syncStatus(connected),'pending')
  assert.equal(syncStatus({...connected,last_success:'2026-11-15'}),'synced')
  assert.equal(syncStatus({...connected,last_success:'2026-11-15',pending:{x:{}}}),'pending')
  assert.equal(syncStatus({...connected,error:'offline'}),'failed')
  assert.equal(syncStatus({...connected,syncing:true,error:'old failure'}),'syncing')
  assert.equal(syncStatus({...connected,enabled:false}),'paused')
})
test('real sync exposes its running state and clears it after failure',async()=>{
  const store=createPreviewStore(), sync={...emptySync(),enabled:true}
  const doc={local:structuredClone(store.state),sync,mappings:{},link:{server:'https://example.com'},tokens:{},iconCache:{}}
  let reject,entered
  const started=new Promise(resolve=>{entered=resolve})
  const transport=()=>({capabilities:()=>{entered();return new Promise((_,fail)=>{reject=fail})}})
  const local=await createLocal(store,{load:async()=>doc,save:async()=>{}},()=>{},transport)
  const running=local.sync()
  await started
  assert.equal(local.status.syncing,true)
  reject(new Error('offline'))
  await assert.rejects(running,/offline/)
  assert.equal(local.status.syncing,false)
  assert.equal(syncStatus(local.status),'failed')
})
test('browser network failures are never shown as raw English text',()=>{
  for (const message of ['Failed to fetch','Load failed','NetworkError when attempting to fetch resource.','net::ERR_NAME_NOT_RESOLVED']) assert.equal(showRawSyncError(message,'zh'),false,message)
  assert.equal(showRawSyncError('令牌已失效，请重新登录','zh'),true)
  assert.equal(showRawSyncError('令牌已失效，请重新登录','en'),false)
})
