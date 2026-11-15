import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'

// Render the actual card template: changes to its inert/visibility bindings must
// preserve the same accessibility contract as the browser's collapsed stack.
const source = await readFile(new URL('./RenewalDesk.vue', import.meta.url), 'utf8')
const template = source.match(/<label v-for="\(s,i\) in items"[\s\S]*?<\/label>/)[0]
async function cards(expanded, busy = false) {
  const app = createSSRApp({ template, setup: () => ({
    expanded, busy, selected: [], keyboard: false, select() {},
    items: Array.from({ length: 4 }, (_, i) => ({ id: i, name: `Card ${i}`, amount: i, currency: 'CNY' })),
    formatAmount: String
  }) })
  app.component('SubIcon', { template: '<span />' })
  return (await renderToString(app)).match(/<label\b[^>]*>/g)
}
test('collapsed card backs are inert and cards beyond the three layers are hidden', async () => {
  const labels = await cards(false)
  assert.ok(!labels[0].includes('inert'))
  for (const label of labels.slice(1)) assert.match(label, /\binert(?:[\s=>]|$)/)
  assert.match(labels[3], /display:none/)
})
test('expanding restores card focus and saving makes all cards inert', async () => {
  assert.ok((await cards(true)).every(label => !label.includes('inert') && !label.includes('display:none')))
  assert.ok((await cards(true, true)).every(label => /\binert/.test(label)))
})
