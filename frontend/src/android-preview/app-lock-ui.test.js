import test from 'node:test'
import assert from 'node:assert/strict'
import { renderClass } from './template-test-helper.js'
const t=key=>key
test('lock screen hides unlock after three cancellations or unavailable device',async()=>{
  for(const [available,cancels,canUnlock] of [[true,0,true],[true,2,true],[true,3,false],[false,0,false]]) {
    const lock={state:{covered:true,booting:false,available,cancels,authenticating:false,reason:'NO_DEVICE_CREDENTIAL',error:'',secret:'PRIVATE_RECORD'}}
    const html=await renderClass('./AppLockScreen.vue','app-lock-screen',{lock,t})
    assert.equal(html.includes('mobile.lockUnlock'),canUnlock);assert.match(html,/mobile.lockExit/);assert.ok(!html.includes('PRIVATE_RECORD'))
  }
})
test('browser app lock settings explain limitations and disable native controls',async()=>{
  const lock={state:{enabled:false,available:false,reason:'PREVIEW',relockMinutes:1,busy:false,settingsError:''}}
  const html=await renderClass('./AppLockSettings.vue','app-lock-settings',{lock,t,changeEnabled(){},changeMinutes(){}})
  assert.match(html,/mobile.lockPreview/);assert.match(html,/<input[^>]+disabled/);assert.match(html,/<select[^>]+disabled/)
})
