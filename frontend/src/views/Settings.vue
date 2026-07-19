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

    <!-- 通知渠道配置（内嵌在设置页） -->
    <NotifyChannels />

    <!-- 提醒与预算 -->
    <div class="card sect">
      <h3>⏰ {{ t('remind.title') }}</h3>
      <div class="row" style="gap:16px;flex-wrap:wrap">
        <div style="flex:1;min-width:150px">
          <label>{{ t('remind.budget') }}（{{ baseCurrency }}）</label>
          <input v-model.number="prefs.monthly_budget" type="number" min="0" :placeholder="t('remind.budgetPh')" />
        </div>
        <div style="flex:1;min-width:120px">
          <label>{{ t('remind.quietStart') }}</label>
          <input v-model="prefs.quiet_start" type="time" />
        </div>
        <div style="flex:1;min-width:120px">
          <label>{{ t('remind.quietEnd') }}</label>
          <input v-model="prefs.quiet_end" type="time" />
        </div>
      </div>
      <p class="muted" style="font-size:12px;margin:6px 0 0">{{ t('remind.quietHint') }}</p>
      <div class="row" style="align-items:center;gap:14px;margin-top:12px;flex-wrap:wrap">
        <label class="switch"><input type="checkbox" v-model="prefs.digest_enabled" /> <span>{{ t('remind.digest') }}</span></label>
        <select v-if="prefs.digest_enabled" v-model.number="prefs.digest_weekday" style="width:auto">
          <option v-for="(d, i) in weekdays" :key="i" :value="i">{{ d }}</option>
        </select>
        <button class="btn" style="width:auto" @click="savePrefs">{{ t('settings.save') }}</button>
      </div>
      <p v-if="prefsMsg" class="ok">{{ prefsMsg }}</p>
    </div>

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

    <!-- 日历订阅 (.ics) -->
    <div class="card sect">
      <h3>📅 {{ t('cal.title') }}</h3>
      <p class="muted" style="font-size:13px;margin-top:0">{{ t('cal.tip') }}</p>
      <div class="row" style="align-items:center;gap:10px">
        <button class="btn ghost" @click="loadCalUrl">🔗 {{ t('cal.get') }}</button>
        <button v-if="calUrl" class="btn ghost" @click="copyCal">📋 {{ t('cal.copy') }}</button>
        <button v-if="calUrl" class="btn ghost" @click="resetCal">♻️ {{ t('cal.reset') }}</button>
      </div>
      <input v-if="calUrl" :value="calUrl" readonly class="cal-url" @focus="$event.target.select()" />
      <p v-if="calMsg" class="ok">{{ calMsg }}</p>
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

      <hr />
      <h4 style="margin:0 0 6px">🗓️ {{ t('autobk.title') }}</h4>
      <p class="muted" style="font-size:13px;margin-top:0">{{ t('autobk.tip') }}</p>
      <div class="row" style="align-items:center;gap:10px">
        <button class="btn ghost" @click="runAutoBackup">▶️ {{ t('autobk.run') }}</button>
        <span class="muted" style="font-size:12px" v-if="autobk">{{ t('autobk.keep', { n: autobk.keep }) }}</span>
      </div>
      <ul v-if="autobk && autobk.files.length" class="bk-list">
        <li v-for="f in autobk.files" :key="f.name"><b>{{ f.name }}</b>
          <span class="muted">{{ (f.size / 1024).toFixed(1) }} KB · {{ fmtTime(f.modified) }}</span></li>
      </ul>
      <p v-else-if="autobk" class="muted" style="font-size:13px">{{ t('autobk.none') }}</p>
    </div>

    <!-- 安全：两步验证 + API Token -->
    <div class="card sect">
      <h3>🔒 {{ t('sec.title') }}</h3>
      <!-- 2FA -->
      <div class="sec-row">
        <div><b>{{ t('sec.twofa') }}</b>
          <span class="muted" style="font-size:12px"> · {{ auth.user?.totp_enabled ? t('sec.on') : t('sec.off') }}</span></div>
        <button v-if="!auth.user?.totp_enabled && !twofa.qr" class="btn ghost sm" @click="twofaSetup">{{ t('sec.enable') }}</button>
        <button v-else-if="auth.user?.totp_enabled" class="btn ghost sm" @click="twofaDisable">{{ t('sec.disable') }}</button>
      </div>
      <div v-if="twofa.qr && !auth.user?.totp_enabled" class="twofa-box">
        <img :src="twofa.qr" class="qr" />
        <div class="twofa-r">
          <p class="muted" style="font-size:13px;margin:0 0 6px">{{ t('sec.scanTip') }}</p>
          <code class="secret">{{ twofa.secret }}</code>
          <div class="row" style="margin-top:8px">
            <input v-model="twofa.code" :placeholder="t('auth.otpPh')" maxlength="6" style="width:130px" />
            <button class="btn sm" @click="twofaEnable">{{ t('sec.confirmEnable') }}</button>
          </div>
        </div>
      </div>
      <p v-if="secMsg" :class="secOk ? 'ok' : 'err'">{{ secMsg }}</p>

      <hr />
      <!-- API Tokens -->
      <div class="sec-row">
        <b>🔑 {{ t('sec.apiTokens') }}</b>
        <div class="row" style="gap:6px">
          <input v-model="newTokenName" :placeholder="t('sec.tokenName')" style="width:130px" />
          <button class="btn ghost sm" @click="createToken">＋</button>
        </div>
      </div>
      <p v-if="createdToken" class="ok" style="word-break:break-all">{{ t('sec.tokenOnce') }}<br /><code>{{ createdToken }}</code></p>
      <ul v-if="tokens.length" class="bk-list">
        <li v-for="tk in tokens" :key="tk.id"><b>{{ tk.name }}</b>
          <span class="muted">{{ tk.masked }} · {{ tk.last_used_at ? fmtTime(tk.last_used_at) : t('sec.neverUsed') }}
            <a href="#" @click.prevent="revokeToken(tk.id)" style="color:var(--danger);margin-left:8px">✕</a></span></li>
      </ul>
    </div>

    <!-- 版本与更新 -->
    <div class="card sect">
      <h3>🚀 {{ t('upd.title') }}</h3>
      <div class="row" style="align-items:center;gap:12px;flex-wrap:wrap">
        <span>{{ t('sys.version') }}：<b>v{{ sys?.version }}</b></span>
        <button class="btn ghost sm" :disabled="updChecking" @click="checkUpdate(true)">🔄 {{ t('upd.check') }}</button>
        <span v-if="upd && !upd.error">
          <b v-if="upd.update_available" class="ok">🎉 {{ t('upd.newVersion', { v: upd.latest }) }}</b>
          <b v-else-if="upd.latest" style="color:var(--success)">✓ {{ t('upd.isLatest') }}</b>
        </span>
        <span v-else-if="upd && upd.error" class="muted" style="font-size:12px">{{ t('upd.failed') }}</span>
      </div>
      <div v-if="upd && upd.update_available" class="upd-box">
        <p style="font-size:13px;margin:0 0 6px">{{ t('upd.howto') }}
          <a :href="upd.release_url" target="_blank" rel="noopener">{{ t('upd.view') }} →</a></p>
        <code>docker compose -f docker-compose.hub.yml pull &amp;&amp; docker compose -f docker-compose.hub.yml up -d</code>
        <p class="muted" style="font-size:12px;margin:6px 0 0">💡 {{ t('upd.backupTip') }}</p>
      </div>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import NotifyChannels from '../components/NotifyChannels.vue'

const { t, locale } = useI18n()
const auth = useAuth()

const themes = [
  { v: 'light', k: 'Light', c: '#ffffff' },
  { v: 'dark', k: 'Dark', c: '#181d2e' },
  { v: 'ocean', k: 'Ocean', c: '#06b6d4' },
  { v: 'forest', k: 'Forest', c: '#16a34a' },
  { v: 'purple', k: 'Purple', c: '#9333ea' },
  { v: 'auto', k: 'Auto', c: 'linear-gradient(135deg,#ffffff 50%,#181d2e 50%)' }
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

const calUrl = ref('')
const calMsg = ref('')
const autobk = ref(null)

const upd = ref(null)
const updChecking = ref(false)
async function checkUpdate(force = false) {
  updChecking.value = true
  try { upd.value = (await api.get('/api/system/version-check', { params: force === true ? { refresh: true } : {} })).data }
  catch { /* ignore */ } finally { updChecking.value = false }
}

const ns = auth.user?.notify_settings || {}
const prefs = reactive({
  monthly_budget: auth.user?.monthly_budget ?? null,
  quiet_start: ns.quiet_start || '',
  quiet_end: ns.quiet_end || '',
  digest_enabled: !!ns.digest_enabled,
  digest_weekday: ns.digest_weekday ?? 0
})
const twofa = reactive({ qr: '', secret: '', code: '' })
const secMsg = ref('')
const secOk = ref(false)
const tokens = ref([])
const newTokenName = ref('')
const createdToken = ref('')

async function twofaSetup() {
  secMsg.value = ''
  try { const { data } = await api.post('/api/me/2fa/setup'); twofa.qr = data.qr; twofa.secret = data.secret }
  catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function twofaEnable() {
  try {
    await api.post('/api/me/2fa/enable', { code: twofa.code })
    twofa.qr = ''; twofa.secret = ''; twofa.code = ''
    await auth.fetchMe(); secOk.value = true; secMsg.value = t('sec.enabledOk')
  } catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function twofaDisable() {
  const pw = window.prompt(t('sec.enterPwd'))
  if (!pw) return
  try { await api.post('/api/me/2fa/disable', { password: pw }); await auth.fetchMe(); secOk.value = true; secMsg.value = t('sec.disabledOk') }
  catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function loadTokens() { try { tokens.value = (await api.get('/api/me/tokens')).data } catch { /* ignore */ } }
async function createToken() {
  if (!newTokenName.value.trim()) return
  try {
    const { data } = await api.post('/api/me/tokens', { name: newTokenName.value.trim() })
    createdToken.value = data.token; newTokenName.value = ''; loadTokens()
  } catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function revokeToken(id) {
  if (!window.confirm(t('sec.revokeConfirm'))) return
  try { await api.delete(`/api/me/tokens/${id}`); loadTokens() } catch { /* ignore */ }
}

const prefsMsg = ref('')
const weekdays = computed(() => [
  t('wk.mon'), t('wk.tue'), t('wk.wed'), t('wk.thu'), t('wk.fri'), t('wk.sat'), t('wk.sun')
])
async function savePrefs() {
  await auth.updateMe({
    monthly_budget: prefs.monthly_budget || null,
    notify_settings: {
      quiet_start: prefs.quiet_start || null, quiet_end: prefs.quiet_end || null,
      digest_enabled: prefs.digest_enabled, digest_weekday: prefs.digest_weekday
    }
  })
  prefsMsg.value = t('settings.saved')
  setTimeout(() => (prefsMsg.value = ''), 3000)
}

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

async function loadCalUrl(reset = false) {
  calMsg.value = ''
  try {
    const { data } = await api.get('/api/calendar/token', { params: reset === true ? { reset: true } : {} })
    calUrl.value = window.location.origin + data.path
  } catch (e) { calMsg.value = e.response?.data?.detail || 'Error' }
}
function resetCal() { loadCalUrl(true).then(() => { calMsg.value = t('cal.resetOk') }) }
async function copyCal() {
  try { await navigator.clipboard.writeText(calUrl.value); calMsg.value = t('cal.copied') }
  catch { calMsg.value = calUrl.value }
}

async function loadAutoBackups() {
  try { autobk.value = (await api.get('/api/backup/auto')).data } catch { /* 非管理员忽略 */ }
}
async function runAutoBackup() {
  try { await api.post('/api/backup/auto/run'); await loadAutoBackups() }
  catch (e) { calMsg.value = e.response?.data?.detail || 'Error' }
}

onMounted(async () => {
  currencies.value = (await api.get('/api/currencies')).data
  sys.value = (await api.get('/api/system/info')).data
  loadRates()
  loadTokens()
  checkUpdate()
  if (auth.user?.is_admin) loadAutoBackups()
})
</script>

<style scoped>
h1 { margin-top: 0; }
.cal-url { width: 100%; margin-top: 10px; font-family: monospace; font-size: 12px; padding: 8px 10px;
  border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); }
.bk-list { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-direction: column; gap: 6px; }
.bk-list li { display: flex; justify-content: space-between; gap: 12px; font-size: 13px;
  padding: 8px 10px; background: var(--surface-2); border-radius: 8px; }
.bk-list .muted { font-size: 12px; }
.sec-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 8px 0; }
.twofa-box { display: flex; gap: 16px; align-items: flex-start; margin: 10px 0; flex-wrap: wrap; }
.twofa-box .qr { width: 150px; height: 150px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.twofa-r { flex: 1; min-width: 200px; }
.secret { display: inline-block; background: var(--surface-2); padding: 4px 8px; border-radius: 6px; font-size: 13px; word-break: break-all; }
.upd-box { margin-top: 12px; padding: 12px; background: var(--surface-2); border-radius: 10px; border: 1px solid var(--border); }
.upd-box code { display: block; background: var(--surface); padding: 8px 10px; border-radius: 8px; font-size: 12px; word-break: break-all; }
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
