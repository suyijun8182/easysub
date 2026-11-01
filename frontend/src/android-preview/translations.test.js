import test from 'node:test'
import assert from 'node:assert/strict'
import { baseCompile } from '@intlify/message-compiler'
import { uiCopy } from './ui-copy.js'
import { syncCopy } from '../sync/copy.js'

test('website and app messages compile with the current Vue I18n version', async () => {
  globalThis.localStorage ||= { getItem: () => null }
  const { default: i18n } = await import('../i18n/index.js')
  const errors = []
  function check(value, path) {
    if (typeof value === 'string') baseCompile(value, { onError: error => errors.push(`${path}: ${error.message}`) })
    else for (const [key, item] of Object.entries(value)) check(item, path + '.' + key)
  }
  for (const locale of ['zh', 'en', 'ru']) {
    check(i18n.global.getLocaleMessage(locale), locale)
    check(uiCopy[locale], locale + '.mobile')
    check(syncCopy[locale], locale + '.sync')
  }
  assert.deepEqual(errors, [])
})
