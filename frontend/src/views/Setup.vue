<template>
  <div class="setup">
    <div class="card setup-card">
      <div class="wordmark"><span class="mark"><i></i></span><span>EasySub</span></div>
      <h1>{{ t('setup.title') }}</h1>
      <p class="sub">{{ t('setup.subtitle') }}</p>

      <label for="st-engine">{{ t('setup.engine') }}</label>
      <select id="st-engine" v-model="cfg.engine" @change="ok = false; msg = ''">
        <option value="sqlite">{{ t('setup.sqlite') }}</option>
        <option value="mysql">{{ t('setup.mysql') }}</option>
      </select>
      <template v-if="cfg.engine === 'mysql'">
      <div class="row">
        <div style="flex:2">
          <label for="st-host">{{ t('setup.host') }}</label>
          <input id="st-host" v-model="cfg.host" placeholder="db / 192.168.1.10" />
        </div>
        <div style="flex:1">
          <label for="st-port">{{ t('setup.port') }}</label>
          <input id="st-port" v-model.number="cfg.port" type="number" class="mono" />
        </div>
      </div>
      <div class="row">
        <div style="flex:1">
          <label for="st-user">{{ t('setup.user') }}</label>
          <input id="st-user" v-model="cfg.user" placeholder="baohao" autocomplete="off" />
        </div>
        <div style="flex:1">
          <label for="st-pwd">{{ t('setup.password') }}</label>
          <input id="st-pwd" v-model="cfg.password" type="password" autocomplete="new-password" />
        </div>
      </div>
      <label for="st-db">{{ t('setup.database') }}</label>
      <input id="st-db" v-model="cfg.database" placeholder="baohao" />

      <p class="tip"><span class="tip-i" v-html="icon('note')"></span><span>{{ t('setup.tip') }}</span></p>
      </template>

      <p v-if="msg" class="note" :class="ok ? 'ok' : 'late'" role="status">{{ msg }}</p>

      <div class="acts">
        <button class="btn ghost" :disabled="busy" @click="testConn">
          {{ testing ? t('setup.testing') : t('setup.test') }}
        </button>
        <button class="btn" :disabled="busy || !ok" @click="save">
          {{ saving ? t('setup.saving') : t('setup.save') }}
        </button>
      </div>

      <div class="lang">
        <button :class="{ on: locale === 'zh' }" @click="setLang('zh')">中文</button>
        <button :class="{ on: locale === 'en' }" @click="setLang('en')">EN</button>
        <button :class="{ on: locale === 'ru' }" @click="setLang('ru')">RU</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { icon } from '../icons'
import axios from 'axios'

const { t, locale } = useI18n()
const cfg = reactive({ engine: 'sqlite', host: 'db', port: 3306, user: 'baohao', password: '', database: 'baohao' })
const payload = () => cfg.engine === 'sqlite' ? { engine: 'sqlite', path: 'data/easysub.db' } : { ...cfg }
const msg = ref('')
const ok = ref(false)
const testing = ref(false)
const saving = ref(false)
const busy = ref(false)

function setLang(l) { locale.value = l; localStorage.setItem('locale', l) }

async function testConn() {
  busy.value = true; testing.value = true; msg.value = ''; ok.value = false
  try {
    const { data } = await axios.post('/api/setup/test', payload())
    ok.value = true; msg.value = `${t('setup.testOk')}: ${data.message || ''}`
  } catch (e) {
    ok.value = false; msg.value = `${t('setup.testFail')}: ${e.response?.data?.detail || e.message}`
  } finally { busy.value = false; testing.value = false }
}

async function save() {
  busy.value = true; saving.value = true; msg.value = ''
  try {
    await axios.post('/api/setup/save', payload())
    msg.value = t('setup.done')
    setTimeout(() => { window.location.href = '/login' }, 800)
  } catch (e) {
    ok.value = false; msg.value = `${e.response?.data?.detail || e.message}`
    busy.value = false; saving.value = false
  }
}
</script>

<style scoped>
.setup { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 16px;
  background: var(--bg); }
.setup-card { width: 100%; max-width: 460px; padding: 28px; }
.wordmark { display: inline-flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px;
  letter-spacing: -.02em; margin-bottom: 22px; }
.mark { width: 30px; height: 30px; border-radius: 9px; background: var(--primary); display: inline-flex;
  align-items: center; padding: 0 6px; flex-shrink: 0; }
.mark i { display: block; height: 4px; width: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--ok-bar) 0 62%, color-mix(in srgb, var(--on-primary) 28%, transparent) 62%); }
h1 { font-size: 22px; margin: 0 0 4px; }
.sub { color: var(--text-soft); font-size: 14px; margin: 0 0 6px; }
.row > div { min-width: 0; }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }

.tip { display: flex; gap: 9px; align-items: flex-start; font-size: 13px; line-height: 1.55; color: var(--text-soft);
  background: var(--surface-2); padding: 10px 12px; border-radius: var(--radius-sm); margin: 16px 0 0; }
.tip-i { display: inline-flex; width: 16px; height: 16px; margin-top: 2px; flex-shrink: 0; color: var(--text-soft); }
.tip-i :deep(svg) { width: 16px; height: 16px; }
.note { font-size: 13px; line-height: 1.5; margin: 12px 0 0; padding: 8px 11px; border-radius: var(--radius-xs);
  overflow-wrap: anywhere; }
.note.ok { background: var(--ok-soft); color: var(--ok); }
.note.late { background: var(--late-soft); color: var(--late); }

.acts { display: flex; gap: 10px; margin-top: 20px; }
.acts .btn { flex: 1; min-height: 42px; }

.lang { display: flex; justify-content: center; gap: 2px; margin-top: 16px; }
.lang button { border: 0; background: transparent; font: inherit; font-size: 13px; color: var(--text-soft);
  min-height: 40px; min-width: 44px; padding: 0 10px; border-radius: var(--radius-xs); cursor: pointer;
  transition: background-color .15s, color .15s; }
.lang button:hover { color: var(--text); background: var(--surface-2); }
.lang button.on { color: var(--text); font-weight: 650; }

@media (max-width: 720px) {
  .setup { align-items: flex-start; padding: 20px 16px calc(20px + env(safe-area-inset-bottom)); }
  .setup-card { padding: 20px 18px; }
  .acts { flex-direction: column-reverse; }
}
</style>
