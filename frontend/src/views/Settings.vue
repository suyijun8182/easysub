<template>
  <div class="settings">
    <header class="page-head">
      <h1>{{ t('settings.title') }}</h1>
    </header>

    <div class="set-grid">
      <!-- 账号与密码 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('users')"></span>{{ t('account.title') }}</h3>
        <div class="pair">
          <div>
            <label>{{ t('account.username') }}</label>
            <input v-model="acc.username" autocomplete="username" />
          </div>
          <div>
            <label>{{ t('account.email') }}</label>
            <input v-model="acc.email" type="email" autocomplete="email" />
          </div>
        </div>
        <div class="actions">
          <button class="btn ghost sm" @click="saveAccount">{{ t('account.saveAccount') }}</button>
        </div>
        <hr />
        <div class="pair">
          <div>
            <label>{{ t('account.oldPwd') }}</label>
            <input v-model="pwd.old_password" type="password" autocomplete="current-password" />
          </div>
          <div>
            <label>{{ t('account.newPwd') }}</label>
            <input v-model="pwd.new_password" type="password" autocomplete="new-password" />
          </div>
        </div>
        <div class="actions">
          <button class="btn ghost sm" @click="changePwd">{{ t('account.changePwd') }}</button>
        </div>
        <p v-if="accMsg" class="msg" :class="accOk ? 'ok' : 'err'">
          <span class="mi" v-html="icon(accOk ? 'check' : 'alert')"></span><span>{{ accMsg }}</span>
        </p>
      </section>

      <!-- 外观与偏好 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('globe')"></span>{{ t('settings.theme') }} / {{ t('settings.language') }}</h3>
        <label>{{ t('settings.language') }}</label>
        <select v-model="locale" @change="changeLocale">
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ru">Русский</option>
        </select>
        <label>{{ t('settings.theme') }}</label>
        <div class="theme-picker" role="radiogroup" :aria-label="t('settings.theme')">
          <button v-for="th in themes" :key="th.v" type="button" class="th" :class="{ on: theme === th.v }"
                  role="radio" :aria-checked="theme === th.v" :title="themeName(th)"
                  @click="theme = th.v; changeTheme()">
            <span class="sw" :style="{ background: th.bg }"><i :style="{ background: th.c }"></i></span>
            <span class="th-n">{{ themeName(th) }}</span>
          </button>
        </div>
        <label>{{ t('settings.baseCurrency') }}</label>
        <select v-model="baseCurrency" @change="changeCurrency">
          <option v-for="c in currencies" :key="c.code" :value="c.code">{{ c.code }} {{ c.symbol }}</option>
        </select>
      </section>

      <!-- 提醒与预算 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('clock')"></span>{{ t('remind.title') }}</h3>
        <div class="trio">
          <div>
            <label>{{ t('remind.budget') }}（{{ baseCurrency }}）</label>
            <input v-model.number="prefs.monthly_budget" type="number" min="0" :placeholder="t('remind.budgetPh')" />
          </div>
          <div>
            <label>{{ t('remind.quietStart') }}</label>
            <input v-model="prefs.quiet_start" type="time" />
          </div>
          <div>
            <label>{{ t('remind.quietEnd') }}</label>
            <input v-model="prefs.quiet_end" type="time" />
          </div>
        </div>
        <p class="muted hint">{{ t('remind.quietHint') }}</p>
        <div class="toggle-row">
          <label class="switch"><input type="checkbox" v-model="prefs.digest_enabled" /> <span>{{ t('remind.digest') }}</span></label>
          <select v-if="prefs.digest_enabled" v-model.number="prefs.digest_weekday" class="auto-w">
            <option v-for="(d, i) in weekdays" :key="i" :value="i">{{ d }}</option>
          </select>
        </div>
        <div class="actions">
          <button class="btn" @click="savePrefs">{{ t('settings.save') }}</button>
          <p v-if="prefsMsg" class="msg ok inline">
            <span class="mi" v-html="icon('check')"></span><span>{{ prefsMsg }}</span>
          </p>
        </div>
      </section>

      <!-- 安全：两步验证 + API Token -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('check')"></span>{{ t('sec.title') }}</h3>
        <!-- 2FA -->
        <input v-model="twofa.password" type="password" autocomplete="current-password" :placeholder="t('sec.enterPwd')" />
        <input v-if="auth.user?.totp_enabled" v-model="twofa.code" :placeholder="t('auth.otpPh')" maxlength="6" inputmode="numeric" />
        <div class="sec-row">
          <div class="sec-l">
            <b>{{ t('sec.twofa') }}</b>
            <span class="tag" :class="{ ok: auth.user?.totp_enabled }">{{ auth.user?.totp_enabled ? t('sec.on') : t('sec.off') }}</span>
          </div>
          <button v-if="!auth.user?.totp_enabled && !twofa.qr" class="btn ghost sm" @click="twofaSetup">{{ t('sec.enable') }}</button>
          <button v-else-if="auth.user?.totp_enabled" class="btn ghost sm" @click="twofaDisable">{{ t('sec.disable') }}</button>
        </div>
        <div v-if="twofa.qr && !auth.user?.totp_enabled" class="twofa-box">
          <img :src="twofa.qr" class="qr" alt="QR" />
          <div class="twofa-r">
            <p class="muted hint top">{{ t('sec.scanTip') }}</p>
            <code class="secret">{{ twofa.secret }}</code>
            <div class="inline-form">
              <input v-model="twofa.code" :placeholder="t('auth.otpPh')" maxlength="6" inputmode="numeric" class="otp" />
              <button class="btn sm" @click="twofaEnable">{{ t('sec.confirmEnable') }}</button>
            </div>
          </div>
        </div>
        <p v-if="secMsg" class="msg" :class="secOk ? 'ok' : 'err'">
          <span class="mi" v-html="icon(secOk ? 'check' : 'alert')"></span><span>{{ secMsg }}</span>
        </p>

        <hr />
        <!-- API Tokens -->
        <div class="sec-row">
          <b>{{ t('sec.apiTokens') }}</b>
          <div class="inline-form">
            <input v-model="newTokenName" :placeholder="t('sec.tokenName')" class="tk-name" />
            <button class="btn ghost sm icon" :title="t('sec.tokenName')" :aria-label="t('sec.tokenName')" @click="createToken">
              <span v-html="icon('plus')"></span>
            </button>
          </div>
        </div>
        <div v-if="createdToken" class="token-once">
          <p class="msg ok"><span class="mi" v-html="icon('check')"></span><span>{{ t('sec.tokenOnce') }}</span></p>
          <code class="code">{{ createdToken }}</code>
        </div>
        <ul v-if="tokens.length" class="item-list">
          <li v-for="tk in tokens" :key="tk.id">
            <div class="il-main">
              <b>{{ tk.name }}</b>
              <span class="muted">{{ tk.masked }} · {{ tk.last_used_at ? fmtTime(tk.last_used_at) : t('sec.neverUsed') }}</span>
            </div>
            <button class="btn ghost danger sm icon" :aria-label="t('sec.revoke')" :title="t('sec.revoke')" @click="revokeToken(tk.id)">
              <span v-html="icon('x')"></span>
            </button>
          </li>
        </ul>
      </section>

      <!-- 通知渠道配置（内嵌在设置页）。包一层边界：某个渠道面板万一渲染出错，
           只坏这一块并显示原因，不会像 debug13 / debug16 那样让整栏静默消失。 -->
      <div class="span-all">
        <ErrorBoundary><NotifyChannels /></ErrorBoundary>
      </div>

      <!-- 常用货币当日汇率 -->
      <section class="card sect">
        <div class="sh-row">
          <h3 class="sh"><span class="hi" v-html="icon('trending')"></span>{{ t('settings.rateTable') }}（{{ rates.base }}）</h3>
          <button class="btn ghost sm" @click="refreshRates"><span v-html="icon('renew')"></span>{{ t('settings.refreshRates') }}</button>
        </div>
        <p class="muted desc">
          {{ t('settings.rateTip', { base: rates.base }) }}
          <span v-if="rates.updated_at"> · {{ t('settings.updatedAt') }} {{ fmtTime(rates.updated_at) }}</span>
          <span v-if="rateMsg" class="rate-msg"> · {{ rateMsg }}</span>
        </p>
        <div v-if="rates.items.length" class="rate-grid">
          <div v-for="r in rates.items" :key="r.code" class="rate">
            <div class="rate-code">{{ r.symbol }} {{ r.code }}</div>
            <div class="rate-val tabular">1 = {{ r.per_unit_in_base }} <span class="muted">{{ rates.base }}</span></div>
          </div>
        </div>
        <p v-else class="muted hint">{{ t('settings.noRates') }}</p>
      </section>

      <!-- 日历订阅 (.ics) -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('calendar')"></span>{{ t('cal.title') }}</h3>
        <p class="muted desc">{{ t('cal.tip') }}</p>
        <div class="actions">
          <button class="btn ghost" @click="loadCalUrl"><span v-html="icon('globe')"></span>{{ t('cal.get') }}</button>
          <button v-if="calUrl" class="btn ghost" @click="copyCal"><span v-html="icon('note')"></span>{{ t('cal.copy') }}</button>
          <button v-if="calUrl" class="btn ghost" @click="resetCal"><span v-html="icon('renew')"></span>{{ t('cal.reset') }}</button>
        </div>
        <input v-if="calUrl" :value="calUrl" readonly class="cal-url" @focus="$event.target.select()" />
        <p v-if="calMsg" class="msg neutral">{{ calMsg }}</p>
      </section>

      <!-- 数据备份与恢复 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('package')"></span>{{ t('backup.title') }}</h3>
        <p class="muted desc">{{ t('backup.tip') }}</p>
        <div class="actions">
          <button class="btn ghost" @click="exportData"><span v-html="icon('download')"></span>{{ t('backup.export') }}</button>
          <label class="btn ghost file-btn"><span v-html="icon('upload')"></span>{{ t('backup.import') }}
            <input type="file" accept="application/json,.json" hidden @change="importData" />
          </label>
        </div>
        <div class="toggle-row">
          <label class="switch"><input type="checkbox" v-model="importReplace" /> <span>{{ t('backup.replace') }}</span></label>
        </div>
        <p v-if="backupMsg" class="msg" :class="backupOk ? 'ok' : 'err'">
          <span class="mi" v-html="icon(backupOk ? 'check' : 'alert')"></span><span>{{ backupMsg }}</span>
        </p>
      </section>

      <!-- 管理员：整站备份与恢复 -->
      <section class="card sect" v-if="auth.user?.is_admin">
        <h3 class="sh"><span class="hi" v-html="icon('library')"></span>{{ t('backupAll.title') }}</h3>
        <p class="muted desc">{{ t('backupAll.tip') }}</p>
        <div class="actions">
          <button class="btn ghost" @click="exportAll"><span v-html="icon('download')"></span>{{ t('backupAll.export') }}</button>
          <label class="btn ghost file-btn"><span v-html="icon('upload')"></span>{{ t('backupAll.import') }}
            <input type="file" accept="application/json,.json" hidden @change="importAll" />
          </label>
        </div>
        <div class="toggle-row">
          <label class="switch"><input type="checkbox" v-model="importAllReplace" /> <span>{{ t('backupAll.replace') }}</span></label>
        </div>
        <p v-if="backupAllMsg" class="msg" :class="backupAllOk ? 'ok' : 'err'">
          <span class="mi" v-html="icon(backupAllOk ? 'check' : 'alert')"></span><span>{{ backupAllMsg }}</span>
        </p>

        <hr />
        <h4 class="sub-h"><span class="hi" v-html="icon('clock')"></span>{{ t('autobk.title') }}</h4>
        <p class="muted desc">{{ t('autobk.tip') }}</p>
        <div class="actions">
          <button class="btn ghost sm" @click="runAutoBackup"><span v-html="icon('package')"></span>{{ t('autobk.run') }}</button>
          <span class="muted hint" v-if="autobk">{{ t('autobk.keep', { n: autobk.keep }) }}</span>
        </div>
        <ul v-if="autobk && autobk.files.length" class="item-list">
          <li v-for="f in autobk.files" :key="f.name">
            <div class="il-main">
              <b>{{ f.name }}</b>
              <span class="muted tabular">{{ (f.size / 1024).toFixed(1) }} KB · {{ fmtTime(f.modified) }}</span>
            </div>
          </li>
        </ul>
        <p v-else-if="autobk" class="muted hint">{{ t('autobk.none') }}</p>
      </section>

      <!-- 版本与更新 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('renew')"></span>{{ t('upd.title') }}</h3>
        <div class="ver-row">
          <span class="ver">{{ t('sys.version') }} <b class="tabular">v{{ sys?.version }}</b></span>
          <button class="btn ghost sm" :disabled="updChecking" @click="checkUpdate(true)">
            <span v-html="icon('renew')"></span>{{ t('upd.check') }}
          </button>
        </div>
        <template v-if="upd && !upd.error">
          <p v-if="upd.update_available" class="msg ok">
            <span class="mi" v-html="icon('sparkle')"></span><b>{{ t('upd.newVersion', { v: upd.latest }) }}</b>
          </p>
          <p v-else-if="upd.latest" class="msg ok">
            <span class="mi" v-html="icon('check')"></span><span>{{ t('upd.isLatest') }}</span>
          </p>
        </template>
        <p v-else-if="upd && upd.error" class="msg neutral">
          <span class="mi" v-html="icon('alert')"></span><span>{{ t('upd.failed') }}</span>
        </p>
        <div v-if="upd && upd.update_available" class="upd-box">
          <p class="upd-how">{{ t('upd.howto') }}
            <a :href="upd.release_url" target="_blank" rel="noopener">{{ t('upd.view') }}</a></p>
          <code class="code">docker compose -f docker-compose.hub.yml pull &amp;&amp; docker compose -f docker-compose.hub.yml up -d</code>
          <p class="muted hint">{{ t('upd.backupTip') }}</p>
        </div>
      </section>

      <!-- 系统信息 -->
      <section class="card sect">
        <h3 class="sh"><span class="hi" v-html="icon('dashboard')"></span>{{ t('sys.title') }}</h3>
        <dl class="kv" v-if="sys">
          <div><dt>{{ t('sys.version') }}</dt><dd>{{ sys.version }}</dd></div>
          <div><dt>{{ t('sys.dbStatus') }}</dt>
            <dd v-if="sys.db_configured" class="db-ok"><span class="dot ok"></span>{{ t('sys.configured') }}</dd>
            <dd v-else>—</dd></div>
          <div><dt>{{ t('sys.serverTime') }}</dt><dd>{{ sys.server_time }}</dd></div>
          <div><dt>{{ t('sys.timezone') }}</dt><dd>{{ sys.timezone }}</dd></div>
          <div><dt>{{ t('sys.scanTime') }}</dt><dd>{{ sys.reminder_scan_time }}</dd></div>
          <div><dt>{{ t('sys.yourSubs') }}</dt><dd>{{ sys.your_subscriptions }}</dd></div>
          <div v-if="sys.total_users != null"><dt>{{ t('sys.totalUsers') }}</dt><dd>{{ sys.total_users }}</dd></div>
          <div v-if="sys.total_subscriptions != null"><dt>{{ t('sys.totalSubs') }}</dt><dd>{{ sys.total_subscriptions }}</dd></div>
        </dl>
        <p v-else class="muted hint">{{ t('common.loading') }}</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import NotifyChannels from '../components/NotifyChannels.vue'
import ErrorBoundary from '../components/ErrorBoundary.vue'
import { icon } from '../icons'

const { t, te, locale } = useI18n()
const auth = useAuth()

// 色板预览：bg = 该主题底色，c = 该主题操作色（与 styles/theme.css 对应）
const themes = [
  { v: 'light', k: 'Light', bg: '#f6f7f5', c: '#1b1f24' },
  { v: 'dark', k: 'Dark', bg: '#171a1e', c: '#eceef0' },
  { v: 'ocean', k: 'Ocean', bg: '#f1f6f8', c: '#0b5d78' },
  { v: 'forest', k: 'Forest', bg: '#f2f5f0', c: '#2f5d3a' },
  { v: 'purple', k: 'Purple', bg: '#f5f3f9', c: '#5b3fc4' },
  { v: 'auto', k: 'Auto', bg: 'linear-gradient(135deg,#f6f7f5 50%,#171a1e 50%)', c: '#8a919b' }
]
// themeAuto 尚无词条时回退显示 Auto，避免把 key 原样显示出来
function themeName(th) { const k = 'settings.theme' + th.k; return te(k) ? t(k) : th.k }

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
const twofa = reactive({ qr: '', secret: '', code: '', password: '' })
const secMsg = ref('')
const secOk = ref(false)
const tokens = ref([])
const newTokenName = ref('')
const createdToken = ref('')

async function twofaSetup() {
  secMsg.value = ''
  try { const { data } = await api.post('/api/me/2fa/setup', { password: twofa.password, code: twofa.code }); twofa.qr = data.qr; twofa.secret = data.secret }
  catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function twofaEnable() {
  try {
    const { data } = await api.post('/api/me/2fa/enable', { code: twofa.code, password: twofa.password })
    auth.acceptSession(data); twofa.password = ''
    twofa.qr = ''; twofa.secret = ''; twofa.code = ''
    await auth.fetchMe(); secOk.value = true; secMsg.value = t('sec.enabledOk')
  } catch (e) { secOk.value = false; secMsg.value = e.response?.data?.detail || 'Error' }
}
async function twofaDisable() {
  if (!twofa.password) return
  try { const { data } = await api.post('/api/me/2fa/disable', { password: twofa.password, code: twofa.code }); auth.acceptSession(data); twofa.password = ''; twofa.code = ''; await auth.fetchMe(); secOk.value = true; secMsg.value = t('sec.disabledOk') }
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

// 读取备份文件：去掉 BOM 再解析；解析失败单独标记，和服务器报错区分开（debug19）
async function readBackupJson(file) {
  const text = (await file.text()).replace(/^﻿/, '')
  try { return JSON.parse(text) } catch { throw { notJson: true } }
}
function importErrText(err) {
  if (err?.notJson) return t('backup.notJson')
  const d = err?.response?.data?.detail
  if (typeof d === 'string' && d) return d
  if (Array.isArray(d) && d.length) return t('backup.httpFail', { s: err.response.status, m: d[0].msg || '' })
  if (err?.response) return t('backup.httpFail', { s: err.response.status, m: String(err.response.statusText || '') })
  return t('backup.netFail')
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
    const json = await readBackupJson(file)
    const { data } = await api.post('/api/backup/import', { data: json, replace: importReplace.value })
    backupOk.value = true
    backupMsg.value = t('backup.importOk', { n: data.imported })
  } catch (err) {
    backupOk.value = false
    backupMsg.value = importErrText(err)
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
    const json = await readBackupJson(file)
    const { data } = await api.post('/api/backup/import-all', { data: json, replace: importAllReplace.value })
    backupAllOk.value = true
    backupAllMsg.value = t('backupAll.importOk', { users: data.users, created: data.created_users, n: data.imported })
  } catch (err) {
    backupAllOk.value = false
    backupAllMsg.value = importErrText(err)
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
    const { data } = await api.post('/api/me/password', pwd)
    auth.acceptSession(data)
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
/* ---------- 布局：桌面两列卡片，通知渠道通栏 ---------- */
.set-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
.set-grid > .card, .set-grid > .span-all :deep(.card) { margin: 0; min-width: 0; }
.span-all { grid-column: 1 / -1; min-width: 0; }

/* ---------- 卡片标题 ---------- */
.sh { display: flex; align-items: center; gap: 9px; margin: 0 0 6px; }
.sh + :not(.desc) { margin-top: 10px; }
.hi { display: inline-flex; width: 18px; height: 18px; flex-shrink: 0; color: var(--text-soft); }
.sh-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.sh-row .sh { margin: 0; }
.sub-h { display: flex; align-items: center; gap: 8px; font-size: 14px; margin: 0 0 4px; }
.sub-h .hi { width: 16px; height: 16px; }
.desc { font-size: 13px; margin: 0 0 14px; line-height: 1.6; }
.hint { font-size: 12.5px; margin: 8px 0 0; line-height: 1.6; }
.hint.top { margin: 0 0 8px; }
hr { border: none; border-top: 1px solid var(--border); margin: 18px 0; }
.sect > label:first-of-type { margin-top: 8px; }

/* ---------- 字段排布 ---------- */
.pair { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 12px; }
.trio { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0 12px; }
.actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.actions .btn span, .ver-row .btn span { display: inline-flex; }
.file-btn { width: auto; margin: 0; color: var(--text); font-size: 14px; font-weight: 550; }
.auto-w { width: auto; min-width: 110px; }
.toggle-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 12px; }

/* ---------- 状态提示 ---------- */
.msg { display: flex; align-items: flex-start; gap: 6px; margin: 12px 0 0; font-size: 13px; line-height: 1.5;
  overflow-wrap: anywhere; }
.msg.inline { margin: 0; align-items: center; }
.msg.ok { color: var(--ok); }
.msg.err { color: var(--late); }
.msg.neutral { color: var(--text-soft); }
.mi { display: inline-flex; width: 15px; height: 15px; flex-shrink: 0; margin-top: 2px; }
.msg.inline .mi { margin-top: 0; }

/* ---------- iOS 风格开关（label.switch > checkbox + 文本） ---------- */
.switch { display: inline-flex; align-items: center; gap: 10px; margin: 0; width: auto; min-height: 40px;
  font-size: 14px; font-weight: 500; color: var(--text); cursor: pointer; user-select: none; }
.switch input { appearance: none; -webkit-appearance: none; position: relative; flex-shrink: 0;
  width: 36px; height: 22px; min-height: 0; margin: 0; padding: 0; border: 0; border-radius: 999px;
  background: var(--border-strong); cursor: pointer; transition: background-color .2s var(--ease-out); }
.switch input::before { content: ''; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px;
  border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25);
  transition: transform .22s var(--ease-out); }
.switch input:checked { background: var(--primary); }
.switch input:checked::before { transform: translateX(14px); background: var(--on-primary); }
.switch input:focus-visible { outline: none; box-shadow: var(--focus); }

/* ---------- 主题色板 ---------- */
.theme-picker { display: grid; grid-template-columns: repeat(auto-fill, minmax(64px, 1fr)); gap: 8px; }
.th { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 8px 4px 6px; min-height: 40px;
  border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); cursor: pointer;
  font: inherit; color: var(--text-soft); transition: border-color .15s, background-color .15s, color .15s; }
.th:hover { border-color: var(--border-strong); color: var(--text); }
.th.on { border-color: var(--primary); color: var(--text); box-shadow: inset 0 0 0 1px var(--primary); }
.sw { position: relative; width: 34px; height: 24px; border-radius: var(--radius-xs);
  box-shadow: inset 0 0 0 1px rgba(0,0,0,.12); overflow: hidden; }
.sw i { position: absolute; right: 4px; bottom: 4px; width: 10px; height: 10px; border-radius: 50%; }
.th-n { font-size: 12px; font-weight: 550; line-height: 1.2; }

/* ---------- 安全 ---------- */
.sec-row { display: flex; justify-content: space-between; align-items: center; gap: 10px 12px; flex-wrap: wrap; }
.sec-l { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.inline-form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 0; }
.twofa-r .inline-form { margin-top: 10px; }
.otp { width: 130px; font-family: var(--mono); letter-spacing: .1em; }
.tk-name { width: 150px; }
.twofa-box { display: flex; gap: 16px; align-items: flex-start; margin: 14px 0 0; flex-wrap: wrap;
  padding: 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface-2); }
.twofa-box .qr { width: 140px; height: 140px; border-radius: var(--radius-xs); background: #fff;
  border: 1px solid var(--border); }
.twofa-r { flex: 1; min-width: 180px; }
.secret, .code { display: block; font-family: var(--mono); font-size: 12.5px; line-height: 1.55;
  padding: 8px 10px; border-radius: var(--radius-xs); background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text); overflow-wrap: anywhere; word-break: break-all; }
.twofa-box .secret { background: var(--surface); }
.token-once { margin-top: 4px; }
.token-once .code { margin-top: 8px; }

/* ---------- 列表（Token / 自动备份） ---------- */
.item-list { list-style: none; padding: 0; margin: 12px 0 0; border: 1px solid var(--border);
  border-radius: var(--radius-sm); overflow: hidden; }
.item-list li { display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 9px 8px 9px 12px; font-size: 13px; }
.item-list li + li { border-top: 1px solid var(--border); }
.il-main { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.il-main b { font-weight: 550; overflow-wrap: anywhere; }
.il-main .muted { font-size: 12px; overflow-wrap: anywhere; }
.item-list .btn span { display: inline-flex; }

/* ---------- 汇率 ---------- */
.rate-msg { color: var(--text); }
.rate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(132px, 1fr)); gap: 8px; }
.rate { border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 9px 12px; background: var(--surface-2); }
.rate-code { font-weight: 600; font-size: 13.5px; }
.rate-val { font-size: 12.5px; color: var(--text); margin-top: 2px; font-variant-numeric: tabular-nums; }

/* ---------- 日历 ---------- */
.cal-url { margin-top: 12px; font-family: var(--mono); font-size: 12.5px; background: var(--surface-2); }

/* ---------- 版本 ---------- */
.ver-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.ver { font-size: 14px; color: var(--text-soft); }
.ver b { color: var(--text); margin-left: 4px; }
.upd-box { margin-top: 12px; padding: 12px 14px; background: var(--surface-2); border-radius: var(--radius-sm);
  border: 1px solid var(--border); }
.upd-how { font-size: 13px; margin: 0 0 8px; }
.upd-box .code { background: var(--surface); }

/* ---------- 系统信息：定义列表 ---------- */
.kv { margin: 6px 0 0; }
.kv > div { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; padding: 9px 0;
  border-bottom: 1px solid var(--border); font-size: 14px; }
.kv > div:last-child { border-bottom: 0; padding-bottom: 0; }
.kv dt { color: var(--text-soft); flex-shrink: 0; }
.kv dd { margin: 0; text-align: right; font-weight: 550; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; min-width: 0; }
.db-ok { display: inline-flex; align-items: center; gap: 7px; }

.tabular { font-variant-numeric: tabular-nums; }

@media (max-width: 900px) {
  .set-grid { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 720px) {
  .set-grid { gap: 12px; }
  .pair { grid-template-columns: minmax(0, 1fr); }
  .btn.sm { min-height: 40px; }
  .btn.sm.icon { width: 40px; }
  .actions .btn, .actions .file-btn { flex: 1 1 auto; }
  .tk-name { flex: 1; width: auto; min-width: 0; }
  .sec-row > .inline-form { width: 100%; flex-wrap: nowrap; }
  .twofa-box { flex-direction: column; align-items: center; }
  .twofa-r { width: 100%; min-width: 0; }
  .otp { flex: 1; width: auto; min-width: 0; }
}
</style>
