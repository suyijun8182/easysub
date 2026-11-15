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
