<template>
  <div class="android-preview">
    <details class="preview-info"><summary>{{ t(preview.isAndroid ? 'sync.nativeApp' : preview.isLocal ? 'sync.app' : 'mobile.previewInfo') }} <span>EasySub</span></summary><p>{{ t(preview.isAndroid ? 'sync.nativeHint' : preview.isLocal ? 'sync.appHint' : 'mobile.previewHint') }}</p></details>
    <router-link v-if="preview.isLocal" class="btn ghost sync-shortcut" to="/settings/sync">{{ t('sync.title') }}</router-link>
    <main ref="main" tabindex="-1" class="app-content"><section v-if="missingRates.length && ['/dashboard','/reports'].includes(route.path)" class="card" role="status"><h2>{{ t('mobile.unknownRate') }}</h2><p>{{ t('mobile.missingRate', { currencies: missingRates.join('、') }) }}</p><router-link to="/settings/currencies" class="btn">{{ t('mobile.manualRate') }}</router-link><router-link to="/subscriptions" class="btn ghost">{{ t('mobile.manage') }}</router-link></section><router-view v-else v-slot="{ Component, route: current }"><Transition name="app-page" mode="out-in" @after-enter="focusPage"><component :is="Component" :key="current.fullPath" /></Transition></router-view></main>
    <nav ref="bottomNav" class="app-bottom" :aria-label="t('sync.nav')"><router-link v-for="item in tabs" :key="item.path" :to="item.path"><span aria-hidden="true" v-html="icon(item.icon)"></span><span>{{ t(item.label) }}</span></router-link></nav>
  </div>
</template>
<script setup>
import { icon } from '../icons.js'
import { useI18n } from 'vue-i18n'
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
const preview = inject('preview'), revision = inject('previewRevision'), route = useRoute()
const main = ref(null)
const bottomNav = ref(null)
let navObserver
function measureViewport() { document.documentElement.style.setProperty('--preview-viewport-height', `${window.visualViewport?.height || window.innerHeight}px`) }
onMounted(() => {
  measureViewport(); window.visualViewport?.addEventListener('resize', measureViewport); window.addEventListener('resize', measureViewport)
  navObserver = new ResizeObserver(() => document.documentElement.style.setProperty('--mobile-nav-height', `${bottomNav.value.getBoundingClientRect().height}px`))
  navObserver.observe(bottomNav.value)
})
onBeforeUnmount(() => { navObserver?.disconnect(); window.visualViewport?.removeEventListener('resize', measureViewport); window.removeEventListener('resize', measureViewport); document.documentElement.style.removeProperty('--preview-viewport-height'); document.documentElement.style.removeProperty('--mobile-nav-height') })
async function focusPage() {
  await nextTick()
  const heading = main.value?.querySelector('h1, h2')
  if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }) }
}
const missingRates = computed(() => {
  revision.value
  return [...new Set([preview.state.user.base_currency, ...preview.state.subscriptions.filter(s => s.is_active).map(s => s.currency)])].filter(c => !(preview.state.rates[c] > 0))
})
const { t } = useI18n()
const tabs = [
  { path: '/dashboard', icon: 'dashboard', label: 'sync.navHome' },
  { path: '/subscriptions', icon: 'subscriptions', label: 'sync.navSubscriptions' },
  { path: '/calendar', icon: 'calendar', label: 'sync.navCalendar' },
  { path: '/reports', icon: 'reports', label: 'sync.navReports' },
  { path: '/settings', icon: 'settings', label: 'sync.navSettings' }
]
</script>
