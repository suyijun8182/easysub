<template>
  <div class="card sect notify">
    <div class="nc-head">
      <div>
        <h3>🔔 {{ t('notifyCfg.title') }}</h3>
        <p class="muted" style="font-size:13px;margin:2px 0 0">Telegram / 飞书 / QQ / Bark / Email / Pushplus / Webhook</p>
      </div>
      <button class="btn" :disabled="saving" @click="save">💾 {{ t('notifyCfg.save') }}</button>
    </div>

    <div class="tabs">
      <button v-for="tb in tabs" :key="tb.key" class="tab" :class="{ on: tab === tb.key }" @click="tab = tb.key">
        {{ tb.label }}<span v-if="cfg[tb.key] && cfg[tb.key].enabled" class="on-dot"></span>
      </button>
    </div>

    <div v-if="loaded" class="panel">
      <div class="ch-head">
        <h4>{{ enableLabel }}</h4>
        <div class="ch-actions">
          <button class="btn ghost sm" :disabled="testing" @click="test(tab)">🔔 {{ t('notifyCfg.test') }}</button>
          <label class="switch"><input type="checkbox" v-model="cfg[tab].enabled" /><span class="track"></span></label>
        </div>
      </div>

      <!-- Telegram -->
      <div v-if="tab === 'telegram'" class="fields">
        <div class="f"><label>BOT TOKEN</label><input v-model="cfg.telegram.bot_token" placeholder="123456:ABC-..." /></div>
        <div class="two">
          <div class="f"><label>CHAT ID</label><input v-model="cfg.telegram.chat_id" placeholder="-100xxxx / 数字" /></div>
          <div class="f"><label>ADMIN ID</label><input v-model="cfg.telegram.admin_id" /></div>
        </div>
        <div class="f"><label>{{ t('notifyCfg.tgApiBase') }}</label><input v-model="cfg.telegram.api_base" placeholder="api.telegram.org" /></div>
        <div class="f"><label>{{ t('notifyCfg.httpProxy') }}</label><input v-model="cfg.telegram.proxy" placeholder="http://127.0.0.1:7890" /></div>
        <div class="row">
          <button class="btn ghost sm" @click="tgAction('me')">{{ t('settings.checkBot') }}</button>
          <button class="btn ghost sm" @click="tgAction('updates')">{{ t('settings.getUpdates') }}</button>
        </div>
      </div>

      <!-- 飞书 -->
      <div v-else-if="tab === 'feishu'" class="fields">
        <div class="two">
          <div class="f"><label>APP ID</label><input v-model="cfg.feishu.app_id" placeholder="cli_xxxx" /></div>
          <div class="f"><label>APP SECRET</label><input v-model="cfg.feishu.app_secret" type="password" /></div>
        </div>
        <div class="f"><label>CHAT IDS</label><input v-model="cfg.feishu.chat_ids" placeholder="oc_xxxx，多个逗号分隔" />
          <small class="muted">{{ t('notifyCfg.feishuHint') }}</small></div>
      </div>

      <!-- QQ -->
      <div v-else-if="tab === 'qq'" class="fields">
        <div class="two">
          <div class="f"><label>APP ID</label><input v-model="cfg.qq.app_id" placeholder="QQ Bot App ID" /></div>
          <div class="f"><label>APP SECRET</label><input v-model="cfg.qq.app_secret" type="password" /></div>
        </div>
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.qqGroups') }}</label><input v-model="cfg.qq.group_ids" placeholder="群聊 OpenID，多个逗号分隔" /></div>
          <div class="f"><label>{{ t('notifyCfg.qqUsers') }}</label><input v-model="cfg.qq.user_ids" placeholder="用户 OpenID，多个逗号分隔" /></div>
        </div>
        <small class="muted">{{ t('notifyCfg.qqHint') }}</small>
      </div>

      <!-- Bark -->
      <div v-else-if="tab === 'bark'" class="fields">
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.targetUrls') }}</label>
            <button class="btn ghost xs" @click="cfg.bark.urls.push('')">+ URL</button></div>
          <p v-if="!cfg.bark.urls.length" class="empty">{{ t('notifyCfg.noBarkUrl') }}</p>
          <div v-for="(u, i) in cfg.bark.urls" :key="i" class="list-row">
            <input v-model="cfg.bark.urls[i]" placeholder="https://api.day.app/你的Key" />
            <button class="x" @click="cfg.bark.urls.splice(i, 1)">✕</button>
          </div>
        </div>
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.barkGroup') }}</label><input v-model="cfg.bark.group" placeholder="EasySub" /></div>
          <div class="f"><label>{{ t('notifyCfg.barkLevel') }}</label>
            <select v-model="cfg.bark.level">
              <option value="active">active</option><option value="timeSensitive">timeSensitive</option>
              <option value="passive">passive</option><option value="critical">critical</option>
            </select></div>
        </div>
        <div class="f"><label>ICON</label><input v-model="cfg.bark.icon" placeholder="图标 URL，可选" /></div>
      </div>

      <!-- Email -->
      <div v-else-if="tab === 'email'" class="fields">
        <div class="three">
          <div class="f"><label>SMTP {{ t('notifyCfg.host') }}</label><input v-model="cfg.email.host" placeholder="smtp.example.com" /></div>
          <div class="f"><label>SMTP {{ t('notifyCfg.port') }}</label><input v-model.number="cfg.email.port" type="number" /></div>
          <div class="f sw"><label>SSL/TLS</label><label class="switch"><input type="checkbox" v-model="cfg.email.ssl" /><span class="track"></span></label></div>
        </div>
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.username') }}</label><input v-model="cfg.email.username" placeholder="邮箱账号" /></div>
          <div class="f"><label>{{ t('notifyCfg.password') }}</label><input v-model="cfg.email.password" type="password" placeholder="密码或授权码" /></div>
        </div>
        <div class="f"><label>{{ t('notifyCfg.from') }}</label><input v-model="cfg.email.from" placeholder="noreply@example.com" /></div>
        <div class="f"><label>{{ t('notifyCfg.to') }}</label><input v-model="cfg.email.to" placeholder="多个收件人用英文逗号分隔" /></div>
      </div>

      <!-- Pushplus -->
      <div v-else-if="tab === 'pushplus'" class="fields">
        <div class="f"><label>TOKEN</label><input v-model="cfg.pushplus.token" placeholder="Pushplus 用户 Token" /></div>
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.ppTopic') }}</label><input v-model="cfg.pushplus.topic" placeholder="群组编码，不填发给个人" /></div>
          <div class="f"><label>{{ t('notifyCfg.ppChannel') }}</label>
            <select v-model="cfg.pushplus.channel">
              <option value="wechat">微信 (wechat)</option><option value="mail">邮件 (mail)</option>
              <option value="webhook">Webhook</option><option value="cp">企业微信 (cp)</option>
            </select></div>
        </div>
      </div>

      <!-- Server酱 -->
      <div v-else-if="tab === 'serverchan'" class="fields">
        <div class="f"><label>SENDKEY</label><input v-model="cfg.serverchan.sendkey" placeholder="SCT... / SendKey" />
          <small class="muted">{{ t('notifyCfg.serverchanHint') }}</small></div>
      </div>

      <!-- 企业微信 -->
      <div v-else-if="tab === 'wecom'" class="fields">
        <div class="f"><label>{{ t('notifyCfg.robotUrl') }}</label><input v-model="cfg.wecom.url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
          <small class="muted">{{ t('notifyCfg.wecomHint') }}</small></div>
      </div>

      <!-- 钉钉 -->
      <div v-else-if="tab === 'dingtalk'" class="fields">
        <div class="f"><label>{{ t('notifyCfg.robotUrl') }}</label><input v-model="cfg.dingtalk.url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." /></div>
        <div class="f"><label>{{ t('notifyCfg.signSecret') }}</label><input v-model="cfg.dingtalk.secret" placeholder="SEC... 加签密钥，选填" />
          <small class="muted">{{ t('notifyCfg.dingtalkHint') }}</small></div>
      </div>

      <!-- Discord -->
      <div v-else-if="tab === 'discord'" class="fields">
        <div class="f"><label>Webhook URL</label><input v-model="cfg.discord.url" placeholder="https://discord.com/api/webhooks/..." />
          <small class="muted">{{ t('notifyCfg.discordHint') }}</small></div>
      </div>

      <!-- Slack -->
      <div v-else-if="tab === 'slack'" class="fields">
        <div class="f"><label>Webhook URL</label><input v-model="cfg.slack.url" placeholder="https://hooks.slack.com/services/..." />
          <small class="muted">{{ t('notifyCfg.slackHint') }}</small></div>
      </div>

      <!-- ntfy -->
      <div v-else-if="tab === 'ntfy'" class="fields">
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.server') }}</label><input v-model="cfg.ntfy.server" placeholder="https://ntfy.sh" /></div>
          <div class="f"><label>Topic</label><input v-model="cfg.ntfy.topic" placeholder="your-topic" /></div>
        </div>
        <div class="f"><label>{{ t('notifyCfg.tokenOptional') }}</label><input v-model="cfg.ntfy.token" placeholder="tk_... 访问令牌，选填" />
          <small class="muted">{{ t('notifyCfg.ntfyHint') }}</small></div>
      </div>

      <!-- Gotify -->
      <div v-else-if="tab === 'gotify'" class="fields">
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.server') }}</label><input v-model="cfg.gotify.server" placeholder="https://gotify.example.com" /></div>
          <div class="f"><label>App Token</label><input v-model="cfg.gotify.token" placeholder="应用 Token" /></div>
        </div>
        <div class="f" style="max-width:160px"><label>{{ t('notifyCfg.priority') }}</label><input v-model.number="cfg.gotify.priority" type="number" /></div>
      </div>

      <!-- Webhook -->
      <div v-else-if="tab === 'webhook'" class="fields">
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.targetUrls') }}</label>
            <button class="btn ghost xs" @click="cfg.webhook.urls.push('')">+ URL</button></div>
          <p v-if="!cfg.webhook.urls.length" class="empty">{{ t('notifyCfg.noWebhookUrl') }}</p>
          <div v-for="(u, i) in cfg.webhook.urls" :key="i" class="list-row">
            <input v-model="cfg.webhook.urls[i]" placeholder="https://example.com/hook" />
            <button class="x" @click="cfg.webhook.urls.splice(i, 1)">✕</button>
          </div>
        </div>
        <div class="f"><label>{{ t('notifyCfg.whSecret') }}</label><input v-model="cfg.webhook.secret" placeholder="HMAC-SHA256 签名密钥，选填" />
          <small class="muted">{{ t('notifyCfg.whSecretHint') }}</small></div>
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.whHeaders') }}</label>
            <button class="btn ghost xs" @click="cfg.webhook.headers.push({ key: '', value: '' })">+ Header</button></div>
          <div v-for="(h, i) in cfg.webhook.headers" :key="i" class="list-row">
            <input v-model="h.key" placeholder="Authorization" style="flex:1" />
            <input v-model="h.value" placeholder="值" style="flex:1.4" />
            <button class="x" @click="cfg.webhook.headers.splice(i, 1)">✕</button>
          </div>
        </div>
        <div class="f"><label>{{ t('notifyCfg.whTemplate') }}</label>
          <textarea v-model="cfg.webhook.template" rows="2" :placeholder="tplPlaceholder"></textarea>
          <small class="muted">{{ t('notifyCfg.whTemplateHint') }}</small></div>
        <div class="two">
          <div class="f"><label>{{ t('notifyCfg.whTimeout') }}</label><input v-model.number="cfg.webhook.timeout_ms" type="number" /></div>
          <div class="f"><label>{{ t('notifyCfg.whRetries') }}</label><input v-model.number="cfg.webhook.max_retries" type="number" /></div>
        </div>
      </div>

      <p v-if="msg" :class="ok ? 'ok' : 'err'">{{ msg }}</p>
    </div>
    <p v-else class="muted">{{ t('common.loading') }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()
const tab = ref('telegram')
const loaded = ref(false)
const saving = ref(false)
const testing = ref(false)
const msg = ref('')
const ok = ref(false)
const cfg = ref(defaults())
const tplPlaceholder = '{{subject}} {{text}}'

const tabs = [
  { key: 'telegram', label: 'Telegram Bot' }, { key: 'feishu', label: '飞书 Bot' },
  { key: 'qq', label: 'QQ Bot' }, { key: 'bark', label: 'Bark' }, { key: 'email', label: 'Email' },
  { key: 'pushplus', label: 'Pushplus' }, { key: 'serverchan', label: 'Server酱' },
  { key: 'wecom', label: '企业微信' }, { key: 'dingtalk', label: '钉钉' },
  { key: 'discord', label: 'Discord' }, { key: 'slack', label: 'Slack' },
  { key: 'ntfy', label: 'ntfy' }, { key: 'gotify', label: 'Gotify' },
  { key: 'webhook', label: 'Webhook' }
]
const enableLabels = {
  telegram: '启用 Telegram 机器人', feishu: '启用飞书机器人', qq: '启用 QQ 机器人',
  bark: '启用 Bark 推送', email: '启用 Email 推送', pushplus: '启用 Pushplus 推送',
  serverchan: '启用 Server酱', wecom: '启用企业微信机器人', dingtalk: '启用钉钉机器人',
  discord: '启用 Discord', slack: '启用 Slack', ntfy: '启用 ntfy', gotify: '启用 Gotify',
  webhook: '启用 Webhook 推送'
}
const enableLabel = computed(() => enableLabels[tab.value])

// 客户端默认结构：与后端保持一致，防止某渠道/字段缺失导致模板访问 undefined（webhook 空白根因防御）
function defaults() {
  return {
    telegram: { enabled: false, bot_token: '', chat_id: '', admin_id: '', api_base: '', proxy: '' },
    feishu: { enabled: false, app_id: '', app_secret: '', chat_ids: '' },
    qq: { enabled: false, app_id: '', app_secret: '', group_ids: '', user_ids: '' },
    bark: { enabled: false, urls: [], group: '', level: 'active', icon: '' },
    email: { enabled: false, host: '', port: 465, ssl: true, username: '', password: '', from: '', to: '' },
    pushplus: { enabled: false, token: '', topic: '', channel: 'wechat' },
    serverchan: { enabled: false, sendkey: '' },
    wecom: { enabled: false, url: '' },
    dingtalk: { enabled: false, url: '', secret: '' },
    discord: { enabled: false, url: '' },
    slack: { enabled: false, url: '' },
    ntfy: { enabled: false, server: 'https://ntfy.sh', topic: '', token: '' },
    gotify: { enabled: false, server: '', token: '', priority: 5 },
    webhook: { enabled: false, urls: [], secret: '', headers: [], template: '', timeout_ms: 5000, max_retries: 3 }
  }
}

function flash(good, text) { ok.value = good; msg.value = text; setTimeout(() => (msg.value = ''), 4000) }

async function load() {
  const base = defaults()
  try {
    const { data } = await api.get('/api/notifications/config')
    const got = data.config || {}
    for (const k of Object.keys(base)) {
      if (got[k] && typeof got[k] === 'object') Object.assign(base[k], got[k])
      // 数组字段确保是数组，避免 v-for over null
      if (!Array.isArray(base[k].urls) && 'urls' in base[k]) base[k].urls = []
      if (k === 'webhook' && !Array.isArray(base[k].headers)) base[k].headers = []
    }
  } catch { /* 用默认值 */ }
  cfg.value = base
  loaded.value = true
}

async function save() {
  saving.value = true
  try {
    await api.put('/api/notifications/config', { config: cfg.value })
    flash(true, t('notifyCfg.saved'))
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') } finally { saving.value = false }
}

async function test(channel) {
  testing.value = true; msg.value = ''
  try {
    await api.post('/api/notifications/test', { channel, config: cfg.value[channel] })
    flash(true, t('notifyCfg.testOk'))
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') } finally { testing.value = false }
}

async function tgAction(kind) {
  msg.value = ''
  try {
    await api.put('/api/notifications/config', { config: cfg.value })
    if (kind === 'me') {
      const { data } = await api.get('/api/notifications/telegram/me')
      flash(true, `${t('settings.botOk')}: @${data.result?.username}`)
    } else {
      const { data } = await api.get('/api/notifications/telegram/updates')
      const ids = (data.result || []).map((u) => u.message?.chat?.id).filter(Boolean)
      if (ids.length) { cfg.value.telegram.chat_id = String(ids[ids.length - 1]); flash(true, 'Chat IDs: ' + [...new Set(ids)].join(', ')) }
      else flash(false, 'No messages yet')
    }
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') }
}

onMounted(load)
</script>

<style scoped>
.notify h3 { margin: 0; }
.nc-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.nc-head .btn { width: auto; }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; padding: 6px; background: var(--surface-2); border-radius: 12px; }
.tab { border: none; background: transparent; padding: 7px 13px; border-radius: 9px; cursor: pointer; font-size: 13px;
  color: var(--text-soft); display: inline-flex; align-items: center; gap: 6px; }
.tab.on { background: var(--surface); color: var(--primary); font-weight: 600; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.on-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.ch-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.ch-head h4 { margin: 0; font-size: 16px; }
.ch-actions { display: flex; align-items: center; gap: 12px; }
.fields { display: flex; flex-direction: column; gap: 13px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 13px; }
.three { display: grid; grid-template-columns: 1fr 1fr auto; gap: 13px; align-items: end; }
.f { display: flex; flex-direction: column; gap: 5px; }
.f.sw { align-items: flex-start; }
.f label { font-size: 12px; font-weight: 600; color: var(--text-soft); letter-spacing: .03em; }
.f-h { display: flex; justify-content: space-between; align-items: center; }
.f small { font-size: 12px; }
.empty { border: 1px dashed var(--border); border-radius: 10px; padding: 12px; text-align: center; color: var(--text-soft); font-size: 13px; margin: 0; }
.list-row { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.list-row input { flex: 1; }
.x { background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; width: 34px; height: 34px; cursor: pointer; color: var(--danger); flex-shrink: 0; }
.btn.sm { width: auto; padding: 7px 12px; font-size: 13px; }
.btn.xs { width: auto; padding: 4px 10px; font-size: 12px; }
.row { display: flex; flex-wrap: wrap; gap: 8px; }
.switch { display: inline-flex; align-items: center; cursor: pointer; }
.switch input { display: none; }
.switch .track { width: 42px; height: 24px; border-radius: 12px; background: var(--border); position: relative; transition: background .2s; }
.switch .track::after { content: ''; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform .2s; }
.switch input:checked + .track { background: var(--primary); }
.switch input:checked + .track::after { transform: translateX(18px); }
.ok { color: var(--success); font-size: 13px; }
.err { color: var(--danger); font-size: 13px; word-break: break-all; }
@media (max-width: 720px) { .two, .three { grid-template-columns: 1fr; } }
</style>
