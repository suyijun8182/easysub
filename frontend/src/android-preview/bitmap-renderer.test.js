import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { createBitmapRenderer, categoryIconName } from './bitmap-renderer.js'
import { icon, setIconRenderer } from '../icons.js'

test('app PNG renderer has independent alpha masks and inherits semantic color', () => {
  const render = createBitmapRenderer({ check:'/assets/check.png', calendar:'/assets/calendar.png' })
  const first = render('check'), second = render('calendar')
  assert.match(first, /href="\/assets\/check\.png"/)
  assert.match(first, /mask-type:alpha/)
  assert.match(first, /fill="currentColor"/)
  assert.match(first, /aria-hidden="true"/)
  assert.notEqual(first.match(/mask id="([^"]+)"/)[1], second.match(/mask id="([^"]+)"/)[1])
  assert.equal(render('missing'), null)
  assert.equal(render('__proto__'), null)
})

test('website keeps its SVG source when the app renderer is not installed', () => {
  const original = icon('check')
  assert.match(original, /polyline/)
  try {
    setIconRenderer(createBitmapRenderer({ check:'/assets/check.png' }))
    assert.match(icon('check'), /data-png-icon="check"/)
    assert.match(icon('calendar'), /<rect/)
    assert.doesNotMatch(icon('calendar'), /data-png-icon/)
  } finally { setIconRenderer(null) }
  assert.equal(icon('check'), original)
})

test('all predefined category glyphs map to available PNGs, custom glyphs stay custom', () => {
  const seed = JSON.parse(fs.readFileSync(new URL('./seed.json',import.meta.url),'utf8'))
  for (const [, glyph] of seed.CATEGORIES) {
    const name = categoryIconName(glyph)
    assert.ok(name, glyph)
    const file = new URL(`../../../assest/debug24/icons/light/${name}.png`,import.meta.url)
    assert.equal(fs.readFileSync(file).subarray(0,8).toString('hex'),'89504e470d0a1a0a')
  }
  assert.equal(categoryIconName('🖥️'), categoryIconName('🖥'))
  assert.equal(categoryIconName('自定义'), null)
  assert.equal(categoryIconName('/preview-icons/provider.png'), null)
})

test('bitmap asset attributes are escaped instead of creating markup', () => {
  const render = createBitmapRenderer({ check:'/asset.png?x=" onload="bad' })
  assert.match(render('check'), /x=&quot; onload=&quot;bad/)
  assert.doesNotMatch(render('check'), / onload="/)
})
