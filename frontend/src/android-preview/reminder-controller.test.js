import test from 'node:test'
import assert from 'node:assert/strict'
import { createReminderController, reminderDestination } from './reminder-controller.js'
function fixture({native=true,enabled=true,required=true}={}) {
  const calls=[], state={}, rows=[{id:7,at:new Date('2030-01-01T09:00:00Z'),title:'Due',body:'Test',extra:{subscriptionId:1,kind:'renewal'}}]
  const plugin={checkPermissions:async()=>({display:enabled?'granted':'denied'}),requestPermissions:async()=>{calls.push('request')},getPending:async()=>({notifications:[{id:3,extra:{easysubKind:'reminder'}},{id:4,extra:{kind:'sync'}}]}),cancel:async o=>calls.push(['cancel',o]),createChannel:async o=>calls.push(['channel',o]),schedule:async o=>calls.push(['schedule',o])}
  const controller=createReminderController({native:()=>native,load:async()=>{calls.push('load');return plugin},nativeStatus:async()=>({enabled,required}),compute:()=>rows,state})
  return {controller,calls,state,rows,plugin}
}
test('browser never loads or calls the notification plugin',async()=>{
  const f=fixture({native:false});await f.controller.rebuild();await f.controller.requestPermission();assert.deepEqual(f.calls,[]);assert.equal(f.state.permission,'preview')
})
test('denied permission computes but never requests or schedules automatically',async()=>{
  const f=fixture({enabled:false});await f.controller.rebuild();assert.equal(f.state.permission,'denied');assert.ok(!f.calls.some(c=>c==='request'||c[0]==='schedule'));assert.equal(f.state.planned,1)
})
test('reschedule cancels owned reminders only, sets private channel and inexact alarms',async()=>{
  const f=fixture();await f.controller.rebuild()
  assert.deepEqual(f.calls.find(c=>c[0]==='cancel')[1],{notifications:[{id:3}]})
  assert.equal(f.calls.find(c=>c[0]==='channel')[1].visibility,0)
  const n=f.calls.find(c=>c[0]==='schedule')[1].notifications[0]
  assert.equal(n.isExactNotification,false);assert.equal(n.extra.easysubKind,'reminder');assert.equal(n.schedule.at,f.rows[0].at)
  assert.equal(f.state.error,false)
})
test('older Android reports no runtime permission needed, explicit request is the only permission prompt',async()=>{
  const f=fixture({required:false});await f.controller.rebuild();assert.equal(f.state.permission,'notRequired');assert.ok(!f.calls.includes('request'))
  await f.controller.requestPermission();assert.ok(f.calls.includes('request'))
})
test('plugin failures become visible state and do not reject saves; later rebuild recovers',async()=>{
  const f=fixture();f.plugin.schedule=async()=>{throw Error('failed')};await f.controller.rebuild();assert.equal(f.state.error,true)
  f.plugin.schedule=async()=>{};await f.controller.rebuild();assert.equal(f.state.error,false)
})
test('deletion cancels prior reminders without writing an empty schedule',async()=>{
  const f=fixture();f.rows.splice(0);await f.controller.rebuild();assert.ok(f.calls.some(c=>c[0]==='cancel'));assert.ok(!f.calls.some(c=>c[0]==='schedule'))
})
test('old Android system notification block overrides granted plugin permission',async()=>{
  const f=fixture({enabled:false,required:false});f.plugin.checkPermissions=async()=>({display:'granted'})
  await f.controller.rebuild();assert.equal(f.state.permission,'denied');assert.equal(f.state.required,false)
  assert.ok(!f.calls.some(c=>c[0]==='schedule'))
})
test('overlapping rebuilds serialize so the last data snapshot wins',async()=>{
  const f=fixture();let unblock, entered
  const ready=new Promise(resolve=>entered=resolve), gate=new Promise(resolve=>unblock=resolve)
  f.plugin.schedule=async()=>{entered();await gate}
  const first=f.controller.rebuild();await ready
  f.rows.splice(0);const second=f.controller.rebuild();unblock();await Promise.all([first,second])
  assert.equal(f.state.planned,0);assert.equal(f.calls.filter(c=>c[0]==='cancel').length,2)
})
test('clicks resolve an existing ID and deleted or malicious IDs go to overview',()=>{
  assert.equal(reminderDestination({subscriptionId:'2'},[{id:2}]),'/subscriptions/2')
  assert.equal(reminderDestination({subscriptionId:3},[{id:2}]),'/dashboard')
  assert.equal(reminderDestination({subscriptionId:'../../settings'},[]),'/dashboard')
})
