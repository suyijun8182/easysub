import { createApp, ref } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import api from '../api/index.js'
import { useAuth } from '../stores/auth.js'
import i18n from '../i18n/index.js'
import { applyTheme } from '../theme.js'
import '@fontsource-variable/onest'
import '../styles/theme.css'
import './mobile.css'
import { createPreviewStore } from './store.js'
import PreviewApp from './PreviewApp.vue'
import { uiCopy } from './ui-copy.js'
import { openStorage } from '../sync/storage.js'
import { createLocal } from '../sync/local.js'
import { syncCopy } from '../sync/copy.js'
import { appearance } from './ui-behavior.js'
import { isAndroid } from '../native/device.js'
for (const [language, messages] of Object.entries(uiCopy)) i18n.global.mergeLocaleMessage(language, { mobile: messages })
for (const [language, messages] of Object.entries(syncCopy)) i18n.global.mergeLocaleMessage(language, { sync: messages })

const store = createPreviewStore()
const revision = ref(0)
const isLocal = isAndroid() || location.pathname.endsWith('/android-app.html')
let local
if (isLocal) {
  try { local = await createLocal(store, await openStorage(), () => { revision.value++ }) }
  catch (error) { document.getElementById('app').textContent = '无法启动本地应用：' + error.message; throw error }
}
export const preview = {
  isLocal,
  isAndroid: isAndroid(),
  get state() { return store.state },
  backup: () => ({ ...store.backup(), ...(local ? { rate_base: local.status.exchange_base } : {}) }),
  async request(...args) { try { return await (local ? local.request(...args) : store.request(...args)) } finally { revision.value++ } },
  restore(...args) { if (local) return local.restore(...args); const result = store.restore(...args); revision.value++; return result }
}
function imageData(file) {
  return new Promise((resolve, reject) => {
    if (file.size > 2 * 1024 * 1024 || !/^image\//.test(file.type)) return reject(new Error('请选择不超过 2 MB 的图片'))
    const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error('无法读取图片')); reader.readAsDataURL(file)
  })
}
// Adapter only exists in this entry. The normal website keeps its own API unchanged.
api.defaults.adapter = async config => {
  try {
    let body = config.data
    if (typeof body === 'string') body = JSON.parse(body || '{}')
    let data
    if (config.url === '/api/icons/upload') data = { url: await imageData(body.get('file')) }
    else if (config.url === '/api/icons/from-url') {
      const url = new URL(body.url)
      if (!['http:', 'https:'].includes(url.protocol)) throw new Error('请输入 http(s) 图片地址')
      const response = await fetch(url, { signal: AbortSignal.timeout(15000), credentials: 'omit' })
      if (!response.ok) throw new Error('图片下载失败')
      data = { url: await imageData(await response.blob()) }
    } else data = await preview.request(config.method, config.url, body || {}, config.params || {})
    return { data, status: 200, statusText: 'OK', headers: {}, config }
  } catch (error) {
    error.config = config; error.response = { status: 400, data: { detail: error.message }, config }; throw error
  }
}
const routes = [
  { path: '/settings/sync', component: () => import('../sync/SyncSettings.vue') },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/Dashboard.vue') }, { path: '/subscriptions', component: () => import('../views/Subscriptions.vue') },
  { path: '/subscriptions/:id', component: () => import('./SubscriptionDetail.vue') },
  { path: '/calendar', component: () => import('../views/Calendar.vue') }, { path: '/reports', component: () => import('../views/Reports.vue') },
  { path: '/notifications', component: () => import('../views/Notifications.vue') }, { path: '/logs', component: () => import('../views/Logs.vue') },
  { path: '/settings/:section?', component: () => import('./MobileSettings.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]
const router = createRouter({ history: createWebHashHistory(), routes, scrollBehavior(to, from, saved) { return saved || { top: 0 } } })
const pinia = createPinia()
const app = createApp(PreviewApp)
app.provide('preview', preview)
app.provide('localSync', local)
app.provide('previewRevision', revision)
app.provide('snapshots', ref([]))
app.use(pinia).use(router).use(i18n)
useAuth(pinia).user = structuredClone(preview.state.user)
const savedAppearance = appearance(preview.state.user)
i18n.global.locale.value = savedAppearance.locale
applyTheme(savedAppearance.theme)
app.mount('#app')
if (local) {
  if (!isAndroid() && import.meta.env.PROD && 'serviceWorker' in navigator) navigator.serviceWorker.register('./local-sw.js').catch(() => {})
  const sync = () => { if (navigator.onLine && document.visibilityState === 'visible') local.sync().catch(() => {}) }
  window.addEventListener('online', sync); document.addEventListener('visibilitychange', sync)
  setInterval(sync, 15000); sync()
  if (isAndroid()) import('../native/lifecycle.js').then(({ setupAndroidLifecycle }) => setupAndroidLifecycle(router, sync)).catch(() => {})
}
