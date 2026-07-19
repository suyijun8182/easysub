import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const routes = [
  { path: '/setup', component: () => import('../views/Setup.vue'), meta: { guest: true, setup: true } },
  { path: '/login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'subscriptions', component: () => import('../views/Subscriptions.vue') },
      { path: 'calendar', component: () => import('../views/Calendar.vue') },
      { path: 'reports', component: () => import('../views/Reports.vue') },
      { path: 'notifications', component: () => import('../views/Notifications.vue') },
      { path: 'notify-settings', component: () => import('../views/NotifySettings.vue') },
      { path: 'logs', component: () => import('../views/Logs.vue') },
      { path: 'settings', component: () => import('../views/Settings.vue') },
      { path: 'users', component: () => import('../views/Users.vue') }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

// 缓存安装状态，避免每次导航都请求（仅缓存「已配置」这一确定结果）
let configured = null
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function checkConfigured() {
  if (configured === true) return true
  // 宿主机重启后端可能正在自愈重连数据库：若磁盘已有配置但引擎暂未就绪，
  // 稍等重试几次，避免误判为「未配置」而错误弹出安装向导。
  for (let i = 0; i < 3; i++) {
    try {
      const { data } = await axios.get('/api/setup/status')
      if (data.configured) { configured = true; return true }
      if (data.config_present) { await sleep(1200); continue }  // 后端自愈中
      return false  // 确为首次安装，未配置
    } catch {
      await sleep(1200)  // 后端暂不可达，重试
    }
  }
  return false
}

router.beforeEach(async (to) => {
  const isConfigured = await checkConfigured()

  // 未配置数据库：强制进入安装向导
  if (!isConfigured) {
    return to.meta.setup ? true : '/setup'
  }
  // 已配置：不再允许访问安装向导
  if (to.meta.setup) return '/login'

  // 登录态校验
  const loggedIn = !!localStorage.getItem('access_token')
  if (!to.meta.guest && !loggedIn) return '/login'
  if (to.meta.guest && loggedIn) return '/dashboard'
})

export default router
