import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { uiCopy } from './ui-copy.js'
import { settingsCopy } from './settings-copy.js'

const themeCss = fs.readFileSync(new URL('../styles/theme.css', import.meta.url), 'utf8')
const mobileCss = fs.readFileSync(new URL('./mobile.css', import.meta.url), 'utf8')
const variables = block => Object.fromEntries([...block.matchAll(/(--[\w-]+)\s*:\s*(#[a-fA-F0-9]{6})\b/g)].map(m => [m[1], m[2]]))
function luminance(hex) {
  const rgb = [1,3,5].map(i => parseInt(hex.slice(i,i+2),16)/255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4)
  return rgb.reduce((total,c,i) => total + c * [.2126,.7152,.0722][i],0)
}
function contrast(a,b) { const values = [luminance(a),luminance(b)].sort((x,y)=>x-y); return (values[1]+.05)/(values[0]+.05) }

test('all five palettes preserve readable content and action text', () => {
  const base = variables(themeCss.match(/:root\s*{([\s\S]*?)}/)[1])
  const mobile = variables(mobileCss.match(/\.android-preview\s*{([\s\S]*?)}/)[1])
  for (const name of ['light','dark','ocean','forest','purple']) {
    const override = name === 'light' ? {} : variables(themeCss.match(new RegExp('\\[data-theme="'+name+'"\\]\\s*{([\\s\\S]*?)}'))[1])
    const dangerOverride = name === 'dark' ? variables(mobileCss.match(/\[data-theme="dark"\] \.android-preview\s*{([^}]*)}/)[1]) : {}
    const tokens = { ...base, ...override, ...mobile, ...dangerOverride }
    for (const [fg,bg] of [['--text','--bg'],['--text-soft','--surface'],['--text-soft','--bg'],['--text-soft','--surface-2'],['--on-primary','--primary'],['--danger-on','--danger-fill'],['--ok','--ok-soft'],['--soon','--soon-soft'],['--late','--late-soft']]) {
      const ratio = contrast(tokens[fg], tokens[bg])
      assert.ok(ratio >= 4.5, `${name}: ${fg} on ${bg} ${ratio.toFixed(2)}:1`)
    }
  }
})

test('new mobile labels have matching Chinese English and Russian keys', () => {
  const keys = Object.keys(uiCopy.zh).sort()
  for (const language of ['en','ru']) {
    assert.deepEqual(Object.keys(uiCopy[language]).sort(), keys)
    for (const value of Object.values(settingsCopy)) assert.ok(value[language]?.trim())
  }
})

test('every cached directory icon is bundled and no oversized download is accepted', () => {
  const cached = JSON.parse(fs.readFileSync(new URL('./cached-icons.json',import.meta.url),'utf8'))
  assert.ok(cached.length > 0)
  for (const slug of cached) {
    const data = fs.readFileSync(new URL(`../../public/preview-icons/${slug}.png`,import.meta.url))
    assert.equal(data.subarray(0,8).toString('hex'),'89504e470d0a1a0a')
    assert.ok(data.byteLength <= 100000)
  }
})
