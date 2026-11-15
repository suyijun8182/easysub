import test from 'node:test'
import assert from 'node:assert/strict'
import { renderClass } from './template-test-helper.js'
const t = (key, args) => key + (args ? ' ' + Object.values(args).join(' ') : '')

test('Android renewal entry is conditional and announces the pending count', async () => {
  const values = { androidPreview: true, renewalCount: 3, t, icon: () => '' }
  const render = () => renderClass('../views/Dashboard.vue', 'mobile-renew-entry', values)
  assert.match(await render(), /3/)
  values.renewalCount = 0
  assert.ok(!(await render()).includes('href'))
  values.renewalCount = 3; values.androidPreview = null
  assert.ok(!(await render()).includes('href'))
})

test('top account entry announces sync status and opens account and sync',async()=>{
 const html=await renderClass('./PreviewApp.vue','mobile-account',{connectionLabel:'Account and sync: Local only',connectionStatus:'local',icon:()=>''})
 assert.match(html,/href="\/settings\/sync"/)
 assert.match(html,/aria-label="Account and sync: Local only"/)
})
test('compact Android cards link to details and expose renewal and edit without deletion or expanded fields',async()=>{
 const subscriptions=[{id:1,name:'DMIT',remark:'Tokyo VPS',amount:20,currency:'USD',billing_type:'recurring',cycle:'month',cycle_count:1,ipv4:'192.0.2.1'}]
 const html=await renderClass('./MobileSubscriptionList.vue','app-subscription-list',{subscriptions,t,statusOf:()=> 'ok',dueText:()=> '369 days',cycleText:()=> 'month'})
 assert.match(html,/href="\/subscriptions\/1"/)
 assert.match(html,/Tokyo VPS/)
 assert.match(html,/sub.renew/);assert.match(html,/sub.edit/)
 assert.ok(!html.includes('192.0.2.1')&&!html.includes('sub.delete')&&!html.includes('life'))
})
test('settings subpage top bar has a named back arrow and the page title',async()=>{
 const html=await renderClass('./SettingsTopBar.vue','app-subpage-bar',{title:'Appearance',t,icon:()=>''})
 assert.match(html,/aria-label="mobile.back"/);assert.match(html,/href="\/settings"/);assert.match(html,/<h1>Appearance<\/h1>/)
})
