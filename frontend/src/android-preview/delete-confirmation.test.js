import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { parse } from '@vue/compiler-dom'
import { parse as parseSFC } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'

const template = async file => parseSFC(await readFile(new URL(file, import.meta.url), 'utf8')).descriptor.template.content
const subscriptions = await template('../views/Subscriptions.vue')
const deletion = parse(subscriptions).children.flatMap(function visit(node) {
  if (node.tag === 'BaseModal' && node.props.some(p => p.exp?.content === 'delTarget || delBulk')) return [node.loc.source]
  return (node.children || []).flatMap(visit)
})[0]
const modal = await template('../components/BaseModal.vue')
const t = key => key.endsWith('.cancel') ? 'Cancel' : key

for (const androidPreview of [true, null]) {
  test(`${androidPreview ? 'Android' : 'website'} delete confirmation renders exactly one cancel button`, async () => {
    const app = createSSRApp({ template: deletion, setup: () => ({
      androidPreview, t, delTarget: { id: 1, name: 'DEVICE_TEST_DELETE' }, delBulk: false,
      deleteRows: [], delErr: '', delPwd: '', deleting: false, selected: new Set(),
      closeDelete() {}, confirmDelete() {}
    }) })
    app.component('BaseModal', { template: modal, setup: () => ({
      androidPreview, t, maskClass: '', page: false, heading: '', submitLabel: '', busy: false,
      titleId: 'delete-title', emit() {}, onKey() {}
    }) })
    const html = await renderToString(app)
    assert.equal((html.match(/<button\b[^>]*>Cancel<\/button>/g) || []).length, 1)
    assert.equal(html.includes('type="password"'), !androidPreview)
  })
}
