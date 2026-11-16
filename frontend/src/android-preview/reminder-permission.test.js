import test from 'node:test'
import assert from 'node:assert/strict'
import { renderClass } from './template-test-helper.js'
const t=key=>key
for(const permission of ['preview','loading','allowed','denied','notRequired']) {
  test(`reminder settings render ${permission} and only denied shows explicit permission actions`,async()=>{
    const html=await renderClass('./ReminderPermission.vue','app-notification-permission',{t,reminders:{state:{permission,error:false,required:true}},request(){},openSettings(){}})
    assert.match(html,new RegExp('mobile.notif_'+permission))
    assert.equal(html.includes('mobile.notifRequest'),permission==='denied')
    assert.equal(html.includes('mobile.notifSettings'),permission==='denied')
  })
}
