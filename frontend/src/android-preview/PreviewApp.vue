<template>
  <div class="android-preview">
    <header v-if="!settingsSubpage" class="mobile-masthead"><router-link to="/dashboard" class="mobile-brand"><span aria-hidden="true" v-html="icon('easysub-mark')"></span>EasySub</router-link><details class="mobile-build"><summary :aria-label="t('sync.nativeApp')">ALPHA</summary><p>{{ t(preview.isAndroid ? 'sync.nativeHint' : preview.isLocal ? 'sync.appHint' : 'mobile.previewHint') }}</p></details><router-link to="/settings/sync" class="mobile-account" :aria-label="connectionLabel"><span aria-hidden="true" v-html="icon('category-cloud')"></span><i class="app-sync-dot" :class="connectionStatus" aria-hidden="true"></i></router-link></header>
    <main ref="main" tabindex="-1" class="app-content"><section v-if="missingRates.length && ['/dashboard','/reports'].includes(route.path)" class="card" role="status"><h2>{{ t('mobile.unknownRate') }}</h2><p>{{ t('mobile.missingRate', { currencies: missingRates.join('、') }) }}</p><router-link to="/settings/currencies" class="btn">{{ t('mobile.manualRate') }}</router-link><router-link to="/subscriptions" class="btn ghost">{{ t('mobile.manage') }}</router-link></section><router-view v-else v-slot="{ Component, route: current }"><component :is="Component" :key="current.fullPath" /></router-view></main>
    <nav ref="bottomNav" class="app-bottom" :aria-label="t('sync.nav')"><router-link v-for="item in tabs" :key="item.path" :to="item.path" custom v-slot="{ href, navigate }"><a :href="href" :class="{ 'router-link-active': selectedTab === item.path }" :aria-current="selectedTab === item.path ? (route.path === item.path ? 'page' : 'location') : undefined" @click="navigateTab($event, item.path, navigate)"><span aria-hidden="true" v-html="icon(item.icon)"></span><span>{{ t(item.label) }}</span></a></router-link></nav>
  </div>
</template>
<script setup>
import { icon } from '../icons.js'
import { useI18n } from 'vue-i18n'
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activeTab } from './ui-behavior.js'
import { syncStatus } from './sync-status.js'
const preview = inject('preview'), revision = inject('previewRevision'), route = useRoute()
const localSync = inject('localSync')
const connectionStatus = computed(() => { revision.value; return syncStatus(localSync?.status) })
const connectionLabel = computed(() => `${t('sync.title')}: ${t('mobile.syncStatus_' + connectionStatus.value)}`)
const settingsSubpage = computed(() => route.path.startsWith('/settings/'))
const main = ref(null)
const selectedTab = computed(() => activeTab(route.path))
const router = useRouter()
let navigationTransition
watch(() => route.fullPath, focusPage, { flush: 'post' })
async function navigateTab(event, path, navigate) {
  if (!document.startViewTransition || event.detail === 0 || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || matchMedia('(prefers-reduced-motion: reduce)').matches || route.path === path) return navigate(event)
  event.preventDefault()
  navigationTransition?.skipTransition()
  const x = event.clientX, y = event.clientY
  const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
  document.documentElement.dataset.deskNavigation = 'true'

  const transition = document.startViewTransition(async () => { await router.push(path); await nextTick() })
  navigationTransition = transition
  try {
    await transition.ready
    // px here are measured viewport coordinates, not design spacing.
    document.documentElement.animate({ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] }, { duration: parseFloat(getComputedStyle(main.value).getPropertyValue('--es-motion-navigation')), easing: getComputedStyle(main.value).getPropertyValue('--es-ease-out').trim(), pseudoElement: '::view-transition-new(root)' })
    await transition.finished
  } catch { /* Navigation remains usable if the platform skips its snapshot. */ }
  finally { if (navigationTransition === transition) { delete document.documentElement.dataset.deskNavigation; navigationTransition = null } }
}
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
const { t, locale } = useI18n()
const tabs = [
  { path: '/dashboard', icon: 'dashboard', label: 'sync.navHome' },
  { path: '/subscriptions', icon: 'subscriptions', label: 'sync.navSubscriptions' },
  { path: '/calendar', icon: 'calendar', label: 'sync.navCalendar' },
  { path: '/reports', icon: 'reports', label: 'sync.navReports' },
  { path: '/settings', icon: 'settings', label: 'sync.navSettings' }
]
</script>
