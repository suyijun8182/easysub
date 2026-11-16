import test from 'node:test'
import assert from 'node:assert/strict'
import { createAppLockController } from './app-lock.js'
const tick=()=>new Promise(resolve=>setImmediate(resolve))
function fixture({enabled=true,available=true,minutes=1,authenticate=async()=>{}}={}) {
  let time=1000, authCalls=0, exits=0, saveError
  const status={enabled,available,relockMinutes:minutes,reason:available?'':'NO_DEVICE_CREDENTIAL'}, state={}
  const lock=createAppLockController({state,native:()=>true,readStatus:async()=>({...status}),authenticate:async()=>{authCalls++;await authenticate()},saveSettings:async value=>{if(saveError)throw saveError;Object.assign(status,value);return {...status}},now:()=>time,exit:()=>{exits++}})
  return {lock,state,status,advance:n=>{time+=n},authCalls:()=>authCalls,exits:()=>exits,setSaveError:value=>{saveError=value}}
}
test('cold start blocks data loading until device authentication resolves',async()=>{
  let approve,loaded=0
  const f=fixture({authenticate:()=>new Promise(resolve=>approve=resolve)})
  const start=f.lock.start().then(()=>loaded++)
  await tick();assert.equal(loaded,0);assert.equal(f.state.covered,true);assert.equal(f.lock.canAccess(),false)
  approve();await start;assert.equal(loaded,1);assert.equal(f.lock.canAccess(),true)
})
test('disabled lock loads without authentication',async()=>{
  const f=fixture({enabled:false});await f.lock.start();assert.equal(f.authCalls(),0);assert.equal(f.lock.canAccess(),true)
})
test('background cover blocks sync and clears without auth before timeout',async()=>{
  const f=fixture();await f.lock.start();f.lock.background();assert.equal(f.lock.canAccess(),false)
  let synced=false;const sync=f.lock.whenUnlocked().then(()=>synced=true)
  f.advance(59999);await f.lock.resume();await sync;assert.equal(synced,true);assert.equal(f.authCalls(),1)
})
test('timeout and immediate mode require authentication on resume',async()=>{
  for(const minutes of [0,1,5,15]) {
    const f=fixture({minutes});await f.lock.start();f.lock.background();f.advance(minutes*60000)
    await f.lock.resume();assert.equal(f.authCalls(),2);assert.equal(f.lock.canAccess(),true)
  }
})
test('three cancellations allow only exit and a new controller starts a new attempt budget',async()=>{
  const f=fixture({authenticate:async()=>{throw {code:'CANCELED'}}});void f.lock.start()
  await tick();await f.lock.unlock();await f.lock.unlock();await f.lock.unlock()
  assert.equal(f.authCalls(),3);assert.equal(f.state.cancels,3);assert.equal(f.lock.canAccess(),false)
  await f.lock.exit();assert.equal(f.exits(),1)
  const fresh=fixture();await fresh.lock.start();assert.equal(fresh.state.cancels,0)
})
test('prompt timeouts and transient errors stay retryable without spending the cancel budget',async()=>{
  for(const code of ['TIMEOUT','UNAVAILABLE']) {
    const f=fixture({authenticate:async()=>{throw {code}}});void f.lock.start()
    await tick();await f.lock.unlock();await f.lock.unlock();await f.lock.unlock();await f.lock.unlock()
    assert.equal(f.state.cancels,0);assert.equal(f.state.error,code);assert.equal(f.authCalls(),5);assert.equal(f.lock.canAccess(),false)
  }
})
test('unavailable device never silently disables an enabled lock',async()=>{
  const f=fixture({available:false});void f.lock.start();await tick();await f.lock.unlock()
  assert.equal(f.state.enabled,true);assert.equal(f.state.available,false);assert.equal(f.authCalls(),0);assert.equal(f.lock.canAccess(),false)
})
test('device credential removal on resume keeps data and sync covered',async()=>{
  const f=fixture();await f.lock.start();f.lock.background();f.status.available=false
  void f.lock.resume();await tick();assert.equal(f.state.enabled,true);assert.equal(f.state.locked,true);assert.equal(f.lock.canAccess(),false)
})
test('configuration success updates state but cancellation preserves settings',async()=>{
  const f=fixture({enabled:false});await f.lock.start();await f.lock.configure(true,5)
  assert.equal(f.state.enabled,true);assert.equal(f.state.relockMinutes,5);assert.equal(f.lock.canAccess(),true)
  f.setSaveError({code:'CANCELED'});await f.lock.configure(false,1)
  assert.equal(f.state.enabled,true);assert.equal(f.state.relockMinutes,5);assert.equal(f.state.settingsError,'CANCELED')
})
test('duplicate foreground events share one authentication attempt',async()=>{
  let attempts=0,approve
  const f=fixture({authenticate:()=>++attempts===1?Promise.resolve():new Promise(resolve=>approve=resolve)})
  await f.lock.start();f.lock.background();f.advance(60000)
  const first=f.lock.resume(), second=f.lock.resume();assert.equal(first,second)
  await tick();assert.equal(f.authCalls(),2);assert.equal(f.lock.canAccess(),false)
  approve();await first;assert.equal(f.lock.canAccess(),true)
})
test('status errors fail closed without invoking authentication or loading data',async()=>{
  const state={},lock=createAppLockController({state,native:()=>true,readStatus:async()=>{throw Error('bridge failed')},authenticate:async()=>assert.fail('No authentication before status'),saveSettings:async()=>{},exit(){}})
  void lock.start();await tick();assert.equal(lock.canAccess(),false);assert.equal(state.covered,true);assert.equal(state.reason,'ERROR')
})
