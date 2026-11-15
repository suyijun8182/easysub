<template>
  <div class="shell">
    <!-- 桌面：左侧导航 -->
    <aside class="sidebar">
      <router-link to="/dashboard" class="brand" aria-label="EasySub">
        <span class="mark" aria-hidden="true"><i></i></span>
        <span class="word">EasySub</span>
      </router-link>

      <nav class="nav" :aria-label="t('nav.dashboard')">
        <router-link v-for="it in navItems" :key="it.to" :to="it.to" class="nav-item">
          <span class="nav-ico" v-html="icon(it.key)"></span>
          <span class="nav-label">{{ t(it.label) }}</span>
        </router-link>
      </nav>

      <div class="spacer"></div>

      <div class="me" v-if="auth.user">
        <span class="avatar" aria-hidden="true">{{ initial }}</span>
        <div class="me-text">
          <div class="uname">{{ auth.user.username }}</div>
          <button class="linkish" @click="logout">{{ t('nav.logout') }}</button>
        </div>
      </div>
      <div class="credit">
        <a href="https://t.me/Aiden_SU" target="_blank" rel="noopener"><span v-html="icon('send')"></span>@Aiden_SU</a>
        <a href="mailto:aidensu8182@gmail.com"><span v-html="icon('mail')"></span>aidensu8182@gmail.com</a>
      </div>
    </aside>

    <main class="content">
      <router-link v-if="auth.user?.insecure_default_password" to="/settings#account" class="password-warning" role="alert">
        {{ t('sec.defaultPasswordWarning') }}
      </router-link>
      <router-link v-if="updateInfo && updateInfo.update_available && !bannerDismissed" to="/settings" class="upd-banner" @click="dismissBanner">
        <span class="upd-ico" v-html="icon('sparkle')"></span>
        <span class="upd-text">{{ t('upd.banner', { v: updateInfo.latest }) }}</span>
        <button class="x" :aria-label="t('common.close')" @click.prevent.stop="dismissBanner" v-html="icon('x')"></button>
      </router-link>
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <!-- 手机：底部标签栏 -->
    <nav class="tabbar" aria-label="tabs">
      <router-link v-for="it in tabItems" :key="it.to" :to="it.to" class="tab">
        <span class="tab-ico" v-html="icon(it.key)"></span>
        <span class="tab-label">{{ t(it.short || it.label) }}</span>
      </router-link>
      <button class="tab" :class="{ active: moreActive }" @click="sheet = true">
        <span class="tab-ico" v-html="icon('more')"></span>
        <span class="tab-label">{{ t('nav.more') }}</span>
      </button>
    </nav>

    <!-- 手机：「更多」面板 -->
    <div v-if="sheet" class="modal-mask" @click.self="sheet = false">
      <div class="modal more-sheet" role="dialog" :aria-label="t('nav.more')">
        <div class="ms-user" v-if="auth.user">
          <span class="avatar" aria-hidden="true">{{ initial }}</span>
          <b>{{ auth.user.username }}</b>
        </div>
        <router-link v-for="it in moreItems" :key="it.to" :to="it.to" class="ms-item" @click="sheet = false">
          <span class="nav-ico" v-html="icon(it.key)"></span>
          <span class="nav-label">{{ t(it.label) }}</span>
          <span class="chev" v-html="icon('chevron')"></span>
        </router-link>
        <button class="ms-item danger" @click="logout">
          <span class="nav-ico" v-html="icon('logout')"></span>
          <span class="nav-label">{{ t('nav.logout') }}</span>
        </button>
        <div class="credit ms-credit">
          <a href="https://t.me/Aiden_SU" target="_blank" rel="noopener"><span v-html="icon('send')"></span>@Aiden_SU</a>
          <a href="mailto:aidensu8182@gmail.com"><span v-html="icon('mail')"></span>aidensu8182@gmail.com</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'

const { t } = useI18n()
const auth = useAuth()
const router = useRouter()
const route = useRoute()
const sheet = ref(false)

const updateInfo = ref(null)
const bannerDismissed = ref(false)
function dismissBanner() {
  bannerDismissed.value = true
  try { sessionStorage.setItem('upd_dismissed', updateInfo.value?.latest || '1') } catch { /* ignore */ }
}
onMounted(async () => {
  try {
    const { data } = await api.get('/api/system/version-check')
    updateInfo.value = data
    if (sessionStorage.getItem('upd_dismissed') === (data.latest || '')) bannerDismissed.value = true
  } catch { /* ignore */ }
})

const initial = computed(() => (auth.user?.username || '?').charAt(0).toUpperCase())

const navItems = computed(() => {
  const base = [
    { to: '/dashboard', key: 'dashboard', label: 'nav.dashboard', tab: true },
    { to: '/subscriptions', key: 'subscriptions', label: 'nav.subscriptions', tab: true },
    { to: '/calendar', key: 'calendar', label: 'nav.calendar', tab: true },
    { to: '/reports', key: 'reports', label: 'nav.reports', tab: true },
    { to: '/notifications', key: 'notifications', label: 'nav.notifications' },
    { to: '/logs', key: 'logs', label: 'nav.logs' },
    { to: '/settings', key: 'settings', label: 'nav.settings' }
  ]
  if (auth.user?.is_admin) base.push({ to: '/users', key: 'users', label: 'nav.users' })
  return base
})
const tabItems = computed(() => navItems.value.filter((x) => x.tab))
const moreItems = computed(() => navItems.value.filter((x) => !x.tab))
const moreActive = computed(() => moreItems.value.some((x) => route.path.startsWith(x.to)))

function logout() {
  sheet.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.password-warning { display: block; margin-bottom: 16px; padding: 12px 16px;
  border: 1px solid var(--danger); border-radius: var(--radius-sm); color: var(--danger);
  background: var(--surface); font-weight: 600; text-decoration: underline; }
.shell { display: grid; grid-template-columns: 236px minmax(0, 1fr); min-height: 100vh;
  /* 侧栏底色随页面高度铺满 */
  background: linear-gradient(90deg, color-mix(in srgb, var(--surface) 55%, var(--bg)) 0 235px, var(--border) 235px 236px, transparent 236px); }

/* ---------- 侧栏 ---------- */
.sidebar { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column;
  padding: 20px 14px 16px; }
.brand { display: flex; align-items: center; gap: 10px; padding: 4px 8px 22px; text-decoration: none; color: var(--text); }
/* 品牌标记：一段正在走完的周期条 */
.mark { width: 30px; height: 30px; border-radius: 9px; background: var(--primary); position: relative;
  display: inline-flex; align-items: center; padding: 0 6px; }
.mark i { display: block; height: 4px; width: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--ok-bar) 0 62%, color-mix(in srgb, var(--on-primary) 28%, transparent) 62%); }
.word { font-weight: 700; font-size: 17px; letter-spacing: -.02em; }

.nav { display: flex; flex-direction: column; gap: 2px; }
.nav-item { position: relative; display: flex; align-items: center; gap: 11px; padding: 8px 10px; min-height: 40px;
  border-radius: var(--radius-sm); color: var(--text-soft); text-decoration: none; font-size: 14px; font-weight: 520;
  transition: background-color .15s, color .15s; }
.nav-ico { width: 18px; height: 18px; display: inline-flex; flex-shrink: 0; }
.nav-ico :deep(svg) { width: 18px; height: 18px; }
.nav-item:hover { background: color-mix(in srgb, var(--surface-2) 80%, transparent); color: var(--text); }
.nav-item.router-link-active { background: var(--surface); color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,.05), 0 0 0 1px var(--border); }
.nav-item.router-link-active::before { content: ''; position: absolute; left: -14px; top: 10px; bottom: 10px;
  width: 3px; border-radius: 0 3px 3px 0; background: var(--primary); }

.spacer { flex: 1; }
.me { display: flex; align-items: center; gap: 10px; padding: 12px 8px; border-top: 1px solid var(--border); }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: var(--primary); color: var(--on-primary); font-weight: 650; font-size: 14px; flex-shrink: 0; }
.me-text { min-width: 0; }
.uname { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.linkish { background: none; border: 0; padding: 0; font: inherit; font-size: 12.5px; color: var(--text-soft); cursor: pointer; }
.linkish:hover { color: var(--late); }
.credit { display: flex; flex-direction: column; gap: 4px; padding: 10px 8px 0; border-top: 1px solid var(--border); }
.credit a { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-soft); text-decoration: none;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-height: 24px; }
.credit a:hover { color: var(--text); }
.credit a :deep(svg) { width: 13px; height: 13px; flex-shrink: 0; }
.credit a > span { display: inline-flex; }

/* ---------- 内容区 ---------- */
.content { min-width: 0; width: 100%; max-width: 1240px; padding: 32px 40px 56px; }
.upd-banner { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding: 10px 12px 10px 14px;
  border-radius: var(--radius-sm); text-decoration: none; color: var(--text); font-size: 14px;
  background: var(--surface); border: 1px solid var(--border); box-shadow: var(--shadow); }
.upd-ico { width: 18px; height: 18px; display: inline-flex; color: var(--ok); }
.upd-text { flex: 1; }
.upd-banner .x { width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center;
  border: 0; background: none; color: var(--text-soft); cursor: pointer; border-radius: 8px; padding: 7px; }
.upd-banner .x:hover { background: var(--surface-2); }

.page-enter-active { transition: opacity .28s var(--ease-out), transform .28s var(--ease-out); }
.page-leave-active { transition: opacity .12s ease; }
.page-enter-from { opacity: 0; transform: translateY(6px); }
.page-leave-to { opacity: 0; }

/* ---------- 手机 ---------- */
.tabbar { display: none; }
@media (max-width: 860px) {
  .shell { display: block; background: none; }
  .sidebar { display: none; }
  .content { padding: calc(18px + env(safe-area-inset-top)) 16px calc(92px + env(safe-area-inset-bottom)); }
  .tabbar { display: grid; grid-template-columns: repeat(5, 1fr); position: fixed; left: 0; right: 0; bottom: 0; z-index: 60;
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom));
    background: color-mix(in srgb, var(--surface) 86%, transparent); border-top: 1px solid var(--border);
    backdrop-filter: blur(16px) saturate(160%); -webkit-backdrop-filter: blur(16px) saturate(160%); }
  .tab { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; min-height: 50px;
    border: 0; background: none; font: inherit; color: var(--text-faint); text-decoration: none; border-radius: 10px; cursor: pointer;
    -webkit-tap-highlight-color: transparent; }
  .tab-ico { width: 23px; height: 23px; display: inline-flex; }
  .tab-ico :deep(svg) { width: 23px; height: 23px; }
  .tab-label { font-size: 11px; font-weight: 550; }
  .tab.router-link-active, .tab.active { color: var(--text); }
  .tab.router-link-active .tab-ico, .tab.active .tab-ico { color: var(--primary); }
  .tab:active { background: var(--surface-2); }
}
.more-sheet { padding-top: 18px; }
.ms-user { display: flex; align-items: center; gap: 10px; padding: 4px 4px 14px; font-size: 15px; }
.ms-item { width: 100%; display: flex; align-items: center; gap: 12px; min-height: 50px; padding: 0 6px;
  border: 0; border-bottom: 1px solid var(--border); background: none; font: inherit; font-size: 15px;
  color: var(--text); text-decoration: none; cursor: pointer; text-align: left; }
.ms-item .nav-label { flex: 1; }
.ms-item .chev { width: 16px; height: 16px; display: inline-flex; color: var(--text-faint); }
.ms-item.router-link-active { color: var(--primary); font-weight: 600; }
.ms-item.danger { color: var(--late); border-bottom: 0; }
.ms-credit { border-top: 0; padding-top: 14px; }
</style>
