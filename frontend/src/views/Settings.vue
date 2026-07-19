<template>
  <div>
    <h1>{{ t('settings.title') }}</h1>

    <div class="grid two">
      <!-- 外观与偏好 -->
      <div class="card sect">
        <h3>🎨 {{ t('settings.theme') }} / {{ t('settings.language') }}</h3>
        <label>{{ t('settings.language') }}</label>
        <select v-model="locale" @change="changeLocale">
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ru">Русский</option>
        </select>
        <label>{{ t('settings.theme') }}</label>
        <div class="theme-picker">
          <button v-for="th in themes" :key="th.v" class="th" :class="{ on: theme === th.v }"
                  :style="{ background: th.c }" :title="t('settings.theme' + th.k)"
                  @click="theme = th.v; changeTheme()"></button>
        </div>
        <label>{{ t('settings.baseCurrency') }}</label>
        <select v-model="baseCurrency" @change="changeCurrency">
          <option v-for="c in currencies" :key="c.code" :value="c.code">{{ c.code }} {{ c.symbol }}</option>
        </select>
      </div>

      <!-- 账号与密码 -->
      <div class="card sect">
        <h3>👤 {{ t('account.title') }}</h3>
        <label>{{ t('account.username') }}</label>
        <input v-model="acc.username" />
        <label>{{ t('account.email') }}</label>
        <input v-model="acc.email" type="email" />
        <button class="btn ghost sm" style="margin-top:10px" @click="saveAccount">{{ t('account.saveAccount') }}</button>
        <hr />
        <label>{{ t('account.oldPwd') }}</label>
        <input v-model="pwd.old_password" type="password" />
        <label>{{ t('account.newPwd') }}</label>
        <input v-model="pwd.new_password" type="password" />
        <button class="btn ghost sm" style="margin-top:10px" @click="changePwd">{{ t('account.changePwd') }}</button>
        <p v-if="accMsg" :class="accOk ? 'ok' : 'err'">{{ accMsg }}</p>
      </div>
    </div>

    <!-- 常用货币当日汇率 -->
    <div class="card sect">
      <div class="tg-head">
        <h3>💱 {{ t('settings.rateTable') }}（{{ rates.base }}）</h3>
        <button class="btn ghost sm" @click="refreshRates">↻ {{ t('settings.refreshRates') }}</button>
      </div>
      <p class="muted" style="font-size:13px;margin-top:0">
        {{ t('settings.rateTip', { base: rates.base }) }}
        <span v-if="rates.updated_at"> · {{ t('settings.updatedAt') }} {{ fmtTime(rates.updated_at) }}</span>
        <span v-if="rateMsg" class="ok"> · {{ rateMsg }}</span>
      </p>
      <div v-if="rates.items.length" class="rate-grid">
        <div v-for="r in rates.items" :key="r.code" class="rate">
          <div class="rate-code">{{ r.symbol }} {{ r.code }}</div>
          <div class="rate-val">1 = {{ r.per_unit_in_base }} <span class="muted">{{ rates.base }}</span></div>
        </div>
      </div>
      <p v-else class="muted">{{ t('settings.noRates') }}</p>
    </div>

    <!-- 通知渠道（已迁移到独立页面） -->
    <router-link to="/notify-settings" class="card sect notify-link">
      <div>
        <h3>🔔 {{ t('settings.telegram') }} / {{ t('nav.notifyConfig') }}</h3>
        <p class="muted" style="font-size:13px;margin:4px 0 0">
          Telegram / 飞书 / QQ / Bark / Email / Pushplus / Webhook —— {{ t('nav.notifyConfig') }} →
        </p>
      </div>
      <span class="arrow">›</span>
    </router-link>

    <!-- 数据备份与恢复 -->
    <div class="card sect">
      <h3>💾 {{ t('backup.title') }}</h3>
      <p class="muted" style="font-size:13px;margin-top:0">{{ t('backup.tip') }}</p>
      <div class="row" style="align-items:center;gap:12px">
        <button class="btn ghost" @click="exportData">⬇️ {{ t('backup.export') }}</button>
        <label class="btn ghost" style="width:auto;margin:0">⬆️ {{ t('backup.import') }}
          <input type="file" accept="application/json,.json" hidden @change="importData" />
        </label>
        <label class="switch"><input type="checkbox" v-model="importReplace" /> <span>{{ t('backup.replace') }}</span></label>
      </div>
      <p v-if="backupMsg" :class="backupOk ? 'ok' : 'err'">{{ backupMsg }}</p>
    </div>

    <!-- 管理员：整站备份与恢复 -->
    <div class="card sect" v-if="auth.user?.is_admin">
      <h3>🗄️ {{ t('backupAll.title') }}</h3>
      <p class="muted" style="font-size:13px;margin-top:0">{{ t('backupAll.tip') }}</p>
      <div class="row" style="align-items:center;gap:12px">
        <button class="btn ghost" @click="exportAll">⬇️ {{ t('backupAll.export') }}</button>
        <label class="btn ghost" style="width:auto;margin:0">⬆️ {{ t('backupAll.import') }}
          <input type="file" accept="application/json,.json" hidden @change="importAll" />
        </label>
        <label class="switch"><input type="checkbox" v-model="importAllReplace" /> <span>{{ t('backupAll.replace') }}</span></label>
      </div>
      <p v-if="backupAllMsg" :class="backupAllOk ? 'ok' : 'err'">{{ backupAllMsg }}</p>
    </div>

    <!-- 系统信息 -->
    <div class="card sect">
      <h3>ℹ️ {{ t('sys.title') }}</h3>
      <div class="sys-grid" v-if="sys">
        <div class="si"><span class="muted">{{ t('sys.version') }}</span><b>{{ sys.version }}</b></div>
        <div class="si"><span class="muted">{{ t('sys.dbStatus') }}</span>
          <b class="ok" v-if="sys.db_configured">● {{ t('sys.configured') }}</b><b v-else>—</b></div>
        <div class="si"><span class="muted">{{ t('sys.serverTime') }}</span><b>{{ sys.server_time }}</b></div>
        <div class="si"><span class="muted">{{ t('sys.timezone') }}</span><b>{{ sys.timezone }}</b></div>
        <div class="si"><span class="muted">{{ t('sys.scanTime') }}</span><b>{{ sys.reminder_scan_time }}</b></div>
        <div class="si"><span class="muted">{{ t('sys.yourSubs') }}</span><b>{{ sys.your_subscriptions }}</b></div>
        <div class="si" v-if="sys.total_users != null"><span class="muted">{{ t('sys.totalUsers') }}</span><b>{{ sys.total_users }}</b></div>
        <div class="si" v-if="sys.total_subscriptions != null"><span class="muted">{{ t('sys.totalSubs') }}</span><b>{{ sys.total_subscriptions }}</b></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'

const { t, locale } = useI18n()
const auth = useAuth()

const themes = [
  { v: 'light', k: 'Light', c: '#ffffff' },
  { v: 'dark', k: 'Dark', c: '#181d2e' },
  { v: 'ocean', k: 'Ocean', c: '#06b6d4' },
  { v: 'forest', k: 'Forest', c: '#16a34a' },
  { v: 'purple', k: 'Purple', c: '#9333ea' }
]

const theme = ref(auth.user?.theme || 'light')
const baseCurrency = ref(auth.user?.base_currency || 'CNY')
const currencies = ref([])
const rateMsg = ref('')
const rates = ref({ base: baseCurrency.value, updated_at: null, items: [] })

const acc = reactive({ username: auth.user?.username || '', email: auth.user?.email || '' })
const pwd = reactive({ old_password: '', new_password: '' })
const accMsg = ref('')
const accOk = ref(false)
const sys = ref(null)

const backupMsg = ref('')
const backupOk = ref(false)
const importReplace = ref(false)

const backupAllMsg = ref('')
const backupAllOk = ref(false)
const importAllReplace = ref(false)

async function exportData() {
  backupMsg.value = ''
  try {
    const { data } = await api.get('/api/backup/export')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 10)
    a.href = url
    a.download = `easysub-backup-${stamp}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    backupOk.value = true
    backupMsg.value = t('backup.exportOk')
  } catch (e) {
    backupOk.value = false
    backupMsg.value = e.response?.data?.detail || 'Error'
  }
}

async function importData(e) {
  const file = e.target.files[0]
  if (!file) return
  backupMsg.value = ''
  if (importReplace.value && !window.confirm(t('backup.replaceConfirm'))) {
    e.target.value = ''
    return
  }
  try {
    const json = JSON.parse(await file.text())
    const { data } = await api.post('/api/backup/import', { data: json, replace: importReplace.value })
    backupOk.value = true
    backupMsg.value = t('backup.importOk', { n: data.imported })
  } catch (err) {
    backupOk.value = false
    backupMsg.value = err.response?.data?.detail || t('backup.importFail')
  } finally {
    e.target.value = ''
  }
}

async function exportAll() {
  backupAllMsg.value = ''
  try {
    const { data } = await api.get('/api/backup/export-all')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 10)
    a.href = url
    a.download = `easysub-full-backup-${stamp}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    backupAllOk.value = true
    backupAllMsg.value = t('backupAll.exportOk', { n: data.users?.length || 0 })
  } catch (e) {
    backupAllOk.value = false
    backupAllMsg.value = e.response?.data?.detail || 'Error'
  }
}

async function importAll(e) {
  const file = e.target.files[0]
  if (!file) return
  backupAllMsg.value = ''
  if (!window.confirm(t(importAllReplace.value ? 'backupAll.replaceConfirm' : 'backupAll.importConfirm'))) {
    e.target.value = ''
    return
  }
  try {
    const json = JSON.parse(await file.text())
    const { data } = await api.post('/api/backup/import-all', { data: json, replace: importAllReplace.value })
    backupAllOk.value = true
    backupAllMsg.value = t('backupAll.importOk', { users: data.users, created: data.created_users, n: data.imported })
  } catch (err) {
    backupAllOk.value = false
    backupAllMsg.value = err.response?.data?.detail || t('backup.importFail')
  } finally {
    e.target.value = ''
  }
}

async function saveAccount() {
  accMsg.value = ''
  try {
    await api.patch('/api/me/account', { username: acc.username, email: acc.email })
    await auth.fetchMe()
    accOk.value = true; accMsg.value = t('account.accountOk')
  } catch (e) { accOk.value = false; accMsg.value = e.response?.data?.detail || 'Error' }
}
async function changePwd() {
  accMsg.value = ''
  try {
    await api.post('/api/me/password', pwd)
    pwd.old_password = ''; pwd.new_password = ''
    accOk.value = true; accMsg.value = t('account.pwdOk')
  } catch (e) { accOk.value = false; accMsg.value = e.response?.data?.detail || 'Error' }
}

async function changeLocale() {
  localStorage.setItem('locale', locale.value)
  await auth.updateMe({ locale: locale.value })
}
async function changeTheme() { await auth.updateMe({ theme: theme.value }) }
async function changeCurrency() {
  await auth.updateMe({ base_currency: baseCurrency.value })
  loadRates()
}

function fmtTime(s) { return s ? new Date(s).toLocaleString() : '' }
async function loadRates() {
  try { rates.value = (await api.get('/api/currencies/rate-table')).data }
  catch { /* ignore */ }
}
async function refreshRates() {
  try {
    await api.post('/api/currencies/rates/refresh')
    rateMsg.value = t('settings.ratesUpdated')
    await loadRates()
  } catch (e) { rateMsg.value = e.response?.data?.detail || 'Error' }
}

onMounted(async () => {
  currencies.value = (await api.get('/api/currencies')).data
  sys.value = (await api.get('/api/system/info')).data
  loadRates()
})
</script>

<style scoped>
h1 { margin-top: 0; }
.notify-link { display: flex; align-items: center; justify-content: space-between; gap: 12px;
  text-decoration: none; color: inherit; transition: border-color .15s ease, transform .15s ease; }
.notify-link:hover { border-color: var(--primary); transform: translateY(-1px); }
.notify-link h3 { margin: 0; }
.notify-link .arrow { font-size: 22px; color: var(--text-soft); }
.two { grid-template-columns: 1fr 1fr; margin-bottom: 16px; }
.sect { margin-bottom: 16px; }
.sect h3 { margin-top: 0; }
hr { border: none; border-top: 1px solid var(--border); margin: 16px 0; }
.ok { color: var(--success); font-size: 13px; }
.err { color: var(--danger); font-size: 13px; word-break: break-all; }
.tg-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.switch { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text-soft); cursor: pointer; width: auto; margin: 0; }
.switch input { width: auto; }
.theme-picker { display: flex; gap: 10px; margin: 6px 0 4px; }
.th { width: 30px; height: 30px; border-radius: 50%; border: 2px solid var(--border); cursor: pointer; padding: 0; }
.th.on { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft); }
.rate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.rate { border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; background: var(--surface-2);
  transition: transform .15s ease, border-color .15s ease; }
.rate:hover { transform: translateY(-2px); border-color: var(--primary); }
.rate-code { font-weight: 600; font-size: 14px; }
.rate-val { font-size: 13px; color: var(--text); margin-top: 3px; }
.sys-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.si { display: flex; flex-direction: column; gap: 3px; padding: 12px; background: var(--surface-2); border-radius: 10px; font-size: 14px; }
.si .muted { font-size: 12px; }
@media (max-width: 720px) { .two { grid-template-columns: 1fr; } }
</style>
