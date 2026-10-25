<template>
  <div class="auth">
    <!-- 品牌面板 -->
    <aside class="brand">
      <div class="brand-in">
        <div class="wordmark"><span class="mark"><i></i></span><span>EasySub</span></div>
        <p class="tagline">{{ t('app.tagline') }}</p>

        <!-- 签名插画：几条正在走完的续费周期（纯装饰） -->
        <div class="demo" aria-hidden="true">
          <div class="demo-row">
            <span class="dot ok"></span><span class="demo-l">SIM</span>
            <div class="life"><i style="width:78%"></i></div>
          </div>
          <div class="demo-row">
            <span class="dot ok"></span><span class="demo-l">Music</span>
            <div class="life"><i style="width:52%;--d:120ms"></i></div>
          </div>
          <div class="demo-row">
            <span class="dot soon"></span><span class="demo-l">VPS</span>
            <div class="life soon"><i style="width:18%;--d:240ms"></i></div>
          </div>
          <div class="demo-row">
            <span class="dot late"></span><span class="demo-l">Cloud</span>
            <div class="life late"><i style="--d:360ms"></i></div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 表单 -->
    <main class="pane">
      <div class="card form">
        <!-- 登录 / 注册 -->
        <form v-if="step === 'form'" novalidate @submit.prevent="submit">
          <div class="seg full">
            <button type="button" :class="{ on: mode === 'login' }" :aria-pressed="mode === 'login'" @click="mode = 'login'">{{ t('auth.login') }}</button>
            <button type="button" :class="{ on: mode === 'register' }" :aria-pressed="mode === 'register'" @click="mode = 'register'">{{ t('auth.register') }}</button>
          </div>

          <label for="au-user">{{ t('auth.username') }}</label>
          <input id="au-user" v-model="username" autocomplete="username" />

          <template v-if="mode === 'register'">
            <label for="au-email">{{ t('auth.email') }}</label>
            <input id="au-email" v-model="email" type="email" autocomplete="email" />
          </template>

          <label for="au-pwd">{{ t('auth.password') }}</label>
          <input id="au-pwd" v-model="password" type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" />

          <template v-if="need2fa">
            <label for="au-otp">{{ t('auth.otp') }}</label>
            <input id="au-otp" v-model="otp" class="code" :placeholder="t('auth.otpPh')" maxlength="6"
              inputmode="numeric" autocomplete="one-time-code" />
          </template>

          <p v-if="error" class="note late" role="alert">{{ error }}</p>
          <p v-if="info" class="note ok" role="status">{{ info }}</p>
          <button type="submit" class="btn block" :disabled="busy">
            {{ mode === 'login' ? t('auth.loginBtn') : t('auth.registerBtn') }}
          </button>
          <a v-if="mode === 'login'" href="#" class="back" @click.prevent="step = 'forgot'">{{ t('auth.forgot') }}</a>
        </form>

        <!-- 忘记密码：发码 -->
        <form v-else-if="step === 'forgot'" novalidate @submit.prevent="doForgot">
          <h2 class="step-t"><span class="ico" v-html="icon('mail')"></span>{{ t('auth.forgotTitle') }}</h2>
          <p class="hint">{{ t('auth.forgotTip') }}</p>
          <label for="au-femail">{{ t('auth.email') }}</label>
          <input id="au-femail" v-model="email" type="email" autocomplete="email" />
          <p v-if="error" class="note late" role="alert">{{ error }}</p>
          <p v-if="info" class="note ok" role="status">{{ info }}</p>
          <button type="submit" class="btn block" :disabled="busy">{{ t('auth.sendCode') }}</button>
          <a href="#" class="back" @click.prevent="backToLogin">{{ t('auth.backToLogin') }}</a>
        </form>

        <!-- 忘记密码：重置 -->
        <form v-else-if="step === 'reset'" novalidate @submit.prevent="doReset">
          <h2 class="step-t"><span class="ico" v-html="icon('edit')"></span>{{ t('auth.resetTitle') }}</h2>
          <label for="au-rcode">{{ t('auth.code') }}</label>
          <input id="au-rcode" v-model="code" class="code" :placeholder="t('auth.codePh')" maxlength="6"
            inputmode="numeric" autocomplete="one-time-code" />
          <label for="au-npwd">{{ t('auth.newPassword') }}</label>
          <input id="au-npwd" v-model="password" type="password" autocomplete="new-password" />
          <p v-if="error" class="note late" role="alert">{{ error }}</p>
          <p v-if="info" class="note ok" role="status">{{ info }}</p>
          <button type="submit" class="btn block" :disabled="busy">{{ t('auth.resetBtn') }}</button>
          <a href="#" class="back" @click.prevent="backToLogin">{{ t('auth.backToLogin') }}</a>
        </form>

        <!-- 邮箱验证码 -->
        <form v-else-if="step === 'verify'" novalidate @submit.prevent="doVerify">
          <h2 class="step-t"><span class="ico" v-html="icon('mail')"></span>{{ t('auth.verifyTitle') }}</h2>
          <p class="hint">{{ t('auth.verifyTip', { email }) }}</p>
          <label for="au-vcode">{{ t('auth.code') }}</label>
          <input id="au-vcode" v-model="code" class="code" :placeholder="t('auth.codePh')" maxlength="6"
            inputmode="numeric" autocomplete="one-time-code" />
          <p v-if="error" class="note late" role="alert">{{ error }}</p>
          <button type="submit" class="btn block" :disabled="busy">
            {{ t('auth.verifyBtn') }}
          </button>
          <a href="#" class="back" @click.prevent="backToLogin">{{ t('auth.backToLogin') }}</a>
        </form>

        <!-- 等待审核 -->
        <template v-else-if="step === 'pending'">
          <h2 class="step-t"><span class="ico soon" v-html="icon('clock')"></span>{{ t('auth.pendingTitle') }}</h2>
          <p class="hint">{{ info || t('auth.pendingMsg') }}</p>
          <button class="btn block" @click="backToLogin">
            {{ t('auth.backToLogin') }}
          </button>
        </template>
      </div>

      <div class="lang">
        <button :class="{ on: locale === 'zh' }" :aria-pressed="locale === 'zh'" lang="zh" @click="setLang('zh')">中文</button>
        <button :class="{ on: locale === 'en' }" :aria-pressed="locale === 'en'" lang="en" @click="setLang('en')">EN</button>
        <button :class="{ on: locale === 'ru' }" :aria-pressed="locale === 'ru'" lang="ru" @click="setLang('ru')">RU</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'

const { t, locale } = useI18n()
const router = useRouter()
const auth = useAuth()

const step = ref('form')      // form | verify | pending | forgot | reset
const mode = ref('login')
const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const otp = ref('')
const need2fa = ref(false)
const error = ref('')
const info = ref('')
const busy = ref(false)

function setLang(l) {
  locale.value = l
  localStorage.setItem('locale', l)
}

function backToLogin() {
  step.value = 'form'; mode.value = 'login'
  error.value = ''; info.value = ''; code.value = ''; otp.value = ''; need2fa.value = false
}

async function doForgot() {
  error.value = ''; info.value = ''; busy.value = true
  try {
    const { data } = await auth.forgot(email.value)
    info.value = data.message
    setTimeout(() => { step.value = 'reset'; info.value = '' }, 1200)
  } catch (e) { error.value = e.response?.data?.detail || 'Error' } finally { busy.value = false }
}
async function doReset() {
  error.value = ''; busy.value = true
  try {
    await auth.reset(email.value, code.value, password.value)
    info.value = t('auth.resetOk'); backToLogin(); info.value = t('auth.resetOk')
  } catch (e) { error.value = e.response?.data?.detail || 'Error' } finally { busy.value = false }
}

async function submit() {
  error.value = ''; info.value = ''
  busy.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value, otp.value)
      router.push('/dashboard')
    } else {
      const res = await auth.register(username.value, email.value, password.value)
      if (res.status === 'verify') { step.value = 'verify' }
      else if (res.status === 'pending') { step.value = 'pending'; info.value = res.message }
      else {
        // 无需验证/审核：直接登录
        try {
          await auth.login(username.value, password.value)
          router.push('/dashboard')
        } catch {
          mode.value = 'login'; info.value = t('auth.registerOk')
        }
      }
    }
  } catch (e) {
    // 需要两步验证：显示 OTP 输入
    if (e.response?.status === 401 && (e.response?.headers?.['x-2fa-required'] || /两步|2fa|OTP/i.test(e.response?.data?.detail || ''))) {
      need2fa.value = true
      error.value = otp.value ? (e.response?.data?.detail || '') : ''
    } else {
      error.value = e.response?.data?.detail || t('auth.loginFail')
    }
  } finally {
    busy.value = false
  }
}

async function doVerify() {
  error.value = ''
  busy.value = true
  try {
    const res = await auth.verifyEmail(email.value, code.value)
    if (res.status === 'pending') { step.value = 'pending'; info.value = res.message }
    else {
      try {
        await auth.login(username.value, password.value)
        router.push('/dashboard')
      } catch {
        step.value = 'form'; mode.value = 'login'; info.value = t('auth.registerOk')
      }
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error'
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.auth { min-height: 100vh; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); background: var(--bg); }

/* ---- 品牌面板 ---- */
.brand { background: var(--surface-2); border-right: 1px solid var(--border); display: flex; align-items: center;
  justify-content: center; padding: 48px 40px; min-width: 0; }
.brand-in { width: 100%; max-width: 400px; }
.wordmark { display: inline-flex; align-items: center; gap: 10px; font-weight: 700; font-size: 19px; letter-spacing: -.02em; }
.mark { width: 30px; height: 30px; border-radius: 9px; background: var(--primary); display: inline-flex;
  align-items: center; padding: 0 6px; flex-shrink: 0; }
.mark i { display: block; height: 4px; width: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--ok-bar) 0 62%, color-mix(in srgb, var(--on-primary) 28%, transparent) 62%); }
.tagline { font-size: 30px; line-height: 1.18; font-weight: 650; letter-spacing: -.025em; margin: 28px 0 36px; }

.demo { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 6px 18px; box-shadow: var(--shadow); }
.demo-row { display: grid; grid-template-columns: 8px 52px minmax(0, 1fr); align-items: center; gap: 10px;
  padding: 13px 0; border-bottom: 1px solid var(--border); }
.demo-row:last-child { border-bottom: 0; }
.demo-l { font-size: 13px; font-weight: 550; color: var(--text-soft); }
.demo .life > i[style*="width"] { right: auto; }

/* ---- 表单面板 ---- */
.pane { display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 40px 24px; gap: 16px; min-width: 0; }
.form { width: 100%; max-width: 380px; padding: 26px; }
.seg.full { display: flex; width: 100%; margin-bottom: 6px; }
.seg.full button { flex: 1; min-height: 36px; }
.step-t { display: flex; align-items: center; gap: 10px; font-size: 18px; margin: 0 0 8px; }
.ico { display: inline-flex; width: 30px; height: 30px; border-radius: var(--radius-xs); align-items: center;
  justify-content: center; background: var(--surface-2); color: var(--text); flex-shrink: 0; }
.ico.soon { background: var(--soon-soft); color: var(--soon); }
.ico :deep(svg) { width: 16px; height: 16px; }
.hint { font-size: 13.5px; line-height: 1.6; color: var(--text-soft); margin: 0 0 4px; overflow-wrap: anywhere; }
.code { font-family: var(--mono); letter-spacing: .2em; font-variant-numeric: tabular-nums; }
.note { font-size: 13px; line-height: 1.5; margin: 12px 0 0; padding: 8px 11px; border-radius: var(--radius-xs);
  overflow-wrap: anywhere; }
.note.late { background: var(--late-soft); color: var(--late); }
.note.ok { background: var(--ok-soft); color: var(--ok); }
.btn.block { width: 100%; margin-top: 18px; min-height: 42px; }
.back { display: inline-flex; align-items: center; min-height: 40px; margin-top: 6px; font-size: 13px; color: var(--text-soft); }
.back:hover { color: var(--text); }

.lang { display: flex; gap: 2px; }
.lang button { border: 0; background: transparent; font: inherit; font-size: 13px; color: var(--text-soft);
  min-height: 40px; min-width: 44px; padding: 0 10px; border-radius: var(--radius-xs); cursor: pointer;
  transition: background-color .15s, color .15s; }
.lang button:hover { color: var(--text); background: var(--surface-2); }
.lang button.on { color: var(--text); font-weight: 650; }

/* ---- 移动端：单列，品牌在上 ---- */
@media (max-width: 860px) {
  .auth { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto 1fr; }
  .brand { border-right: 0; border-bottom: 1px solid var(--border); padding: 28px 20px 24px; }
  .brand-in { max-width: 420px; }
  .tagline { font-size: 22px; margin: 16px 0 20px; }
  .pane { justify-content: flex-start; padding: 24px 16px calc(24px + env(safe-area-inset-bottom)); }
  .form { max-width: 420px; }
}
@media (max-width: 720px) {
  .brand { padding: 22px 16px 18px; }
  .tagline { margin: 12px 0 0; font-size: 20px; }
  .demo { display: none; }
  .form { padding: 20px 18px; }
  .seg.full button { min-height: 40px; }
}
</style>
