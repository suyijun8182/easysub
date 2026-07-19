<template>
  <div class="shell">
    <!-- 移动端顶部栏 -->
    <header class="topbar">
      <button class="hamb" @click="drawer = true" aria-label="menu">☰</button>
      <div class="brand sm">🔔 {{ t('app.title') }}</div>
      <div style="width:38px"></div>
    </header>

    <!-- 遮罩（移动端抽屉打开时） -->
    <div v-if="drawer" class="drawer-mask" @click="drawer = false"></div>

    <aside class="sidebar" :class="{ open: drawer }">
      <div class="brand">🔔 {{ t('app.title') }}</div>
      <nav @click="drawer = false">
        <router-link v-for="it in navItems" :key="it.to" :to="it.to" class="nav-card">
          <span class="nav-ico" v-html="icon(it.key)"></span>
          <span class="nav-label">{{ t(it.label) }}</span>
          <span class="nav-arrow">›</span>
        </router-link>
      </nav>
      <div class="spacer"></div>
      <div class="user" v-if="auth.user">
        <div class="uname">{{ auth.user.username }}</div>
        <a href="#" @click.prevent="logout">🚪 {{ t('nav.logout') }}</a>
      </div>
      <div class="credit">
        <a href="https://t.me/Aiden_SU" target="_blank" rel="noopener">✈️ TG @Aiden_SU</a>
        <a href="mailto:aidensu8182@gmail.com">✉️ aidensu8182@gmail.com</a>
      </div>
    </aside>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'

const { t } = useI18n()
const auth = useAuth()
const router = useRouter()
const drawer = ref(false)

const navItems = computed(() => {
  const base = [
    { to: '/dashboard', key: 'dashboard', label: 'nav.dashboard' },
    { to: '/subscriptions', key: 'subscriptions', label: 'nav.subscriptions' },
    { to: '/calendar', key: 'calendar', label: 'nav.calendar' },
    { to: '/reports', key: 'reports', label: 'nav.reports' },
    { to: '/notifications', key: 'notifications', label: 'nav.notifications' },
    { to: '/logs', key: 'logs', label: 'nav.logs' },
    { to: '/settings', key: 'settings', label: 'nav.settings' }
  ]
  if (auth.user?.is_admin) base.push({ to: '/users', key: 'users', label: 'nav.users' })
  return base
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.shell { display: flex; min-height: 100vh; }
.sidebar { width: 230px; background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 18px 14px; position: sticky; top: 0; height: 100vh; z-index: 50; }
.brand { font-weight: 700; font-size: 16px; margin-bottom: 22px;
  background: linear-gradient(135deg, var(--primary), var(--primary-2));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
nav { display: flex; flex-direction: column; gap: 7px; }
.nav-card { display: flex; align-items: center; gap: 10px; padding: 9px 11px; border-radius: 12px;
  color: var(--text); font-size: 14px; border: 1px solid transparent; background: var(--surface-2);
  transition: transform .15s ease, background .15s ease, box-shadow .2s ease, border-color .15s ease; }
.nav-ico { width: 30px; height: 30px; border-radius: 9px; display: flex; align-items: center;
  justify-content: center; background: var(--surface); border: 1px solid var(--border);
  flex-shrink: 0; transition: transform .2s ease; color: var(--text-soft); }
.nav-ico :deep(svg) { width: 17px; height: 17px; }
.nav-card:hover .nav-ico { color: var(--primary); }
.nav-card.router-link-active .nav-ico { color: #fff; }
.nav-label { flex: 1; font-weight: 500; }
.nav-arrow { color: var(--text-soft); opacity: 0; transform: translateX(-4px); transition: all .2s ease; }
.nav-card:hover { transform: translateX(3px); background: var(--primary-soft); border-color: color-mix(in srgb, var(--primary) 30%, var(--border)); }
.nav-card:hover .nav-ico { transform: scale(1.1) rotate(-4deg); }
.nav-card:hover .nav-arrow { opacity: 1; transform: translateX(0); }
.nav-card.router-link-active { background: linear-gradient(135deg, var(--primary), var(--primary-2));
  color: #fff; box-shadow: 0 6px 16px rgba(91,91,214,.32); border-color: transparent; }
.nav-card.router-link-active .nav-ico { background: rgba(255,255,255,.22); border-color: transparent; }
.nav-card.router-link-active .nav-arrow { opacity: 1; transform: translateX(0); color: #fff; }
.spacer { flex: 1; }
.user { font-size: 13px; color: var(--text-soft); border-top: 1px solid var(--border); padding-top: 12px; }
.user .uname { font-weight: 600; color: var(--text); }
.user a { display: block; margin-top: 6px; }
.credit { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 5px; }
.credit a { font-size: 12px; color: var(--text-soft); display: flex; align-items: center; gap: 5px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color .15s ease; }
.credit a:hover { color: var(--primary); }
.content { flex: 1; padding: 26px 32px; max-width: 1200px; width: 100%; }

/* 顶部栏 + 抽屉遮罩仅移动端出现 */
.topbar { display: none; }
.drawer-mask { display: none; }

@media (max-width: 720px) {
  .shell { flex-direction: column; }
  .topbar { display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 45; background: var(--surface);
    border-bottom: 1px solid var(--border); padding: 10px 14px; }
  .topbar .brand.sm { margin: 0; font-size: 15px; }
  .hamb { width: 38px; height: 38px; border: none; background: transparent;
    font-size: 20px; color: var(--text); cursor: pointer; }
  .drawer-mask { display: block; position: fixed; inset: 0; background: rgba(15,18,35,.45);
    z-index: 48; }
  .sidebar { position: fixed; top: 0; left: 0; height: 100vh; width: 250px;
    transform: translateX(-110%); transition: transform .25s ease; box-shadow: var(--shadow-lg); }
  .sidebar.open { transform: translateX(0); }
  .content { padding: 16px 14px; }
}
</style>
