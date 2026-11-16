import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { parse as parseSFC } from '@vue/compiler-sfc'
import { parse } from '@vue/compiler-dom'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { preferenceDraft, preferencePatch } from './preference-draft.js'

test('null notification settings render the actual reminders form with empty quiet hours',async()=>{
  const user={locale:'zh',notify_settings:null}, prefs=preferenceDraft(user)
  const source=await readFile(new URL('./MobileSettings.vue',import.meta.url),'utf8')
  const template=parseSFC(source).descriptor.template.content
  function find(node) {
    if(node.tag==='form' && node.props.some(p=>p.exp?.content==="section === 'reminders'"))return node.loc.source.replace('v-else-if="section === \'reminders\'"','')
    for(const child of node.children||[]) {const result=find(child);if(result)return result}
  }
  const app=createSSRApp({template:find(parse(template)),setup:()=>({prefs,savePrefs(){},text:s=>s,t:s=>s})})
  app.component('ReminderPermission',{template:'<section>System notification permissions</section>'})
  const html=await renderToString(app)
  assert.equal((html.match(/type="time"/g)||[]).length,2)
  assert.ok(!html.includes('22:00')&&!html.includes('08:00'));assert.match(html,/System notification permissions/)
  assert.equal(user.notify_settings,null)
})
test('untouched null or partial settings are omitted when saving any preferences',()=>{
  for(const notify_settings of [null,undefined,{}, {quiet_start:'12:00',custom_flag:true}]) {
    const draft=preferenceDraft({notify_settings,locale:'zh',monthly_budget:null}), saved=structuredClone(draft)
    draft.locale='en'
    assert.ok(!Object.hasOwn(preferencePatch(draft,saved),'notify_settings'))
    assert.equal(preferencePatch(draft,saved).locale,'en')
    draft.notify_settings.quiet_start='21:00'
    assert.equal(preferencePatch(draft,saved).notify_settings.quiet_start,'21:00')
    draft.notify_settings=structuredClone(saved.notify_settings)
    assert.ok(!Object.hasOwn(preferencePatch(draft,saved),'notify_settings'))
  }
})
