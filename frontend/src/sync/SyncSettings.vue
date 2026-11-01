<template>
  <div class="sync-settings" :aria-busy="busy">
    <header class="page-head"><h1>{{ t('sync.title') }}</h1><router-link class="btn ghost" to="/settings">{{ t('mobile.back') }}</router-link></header>
    <p v-if="!local" class="card">{{ t('sync.previewHint') }} <a href="/android-app.html#/settings/sync">{{ t('sync.openLocal') }}</a></p>
    <template v-else>
      <section class="card">
        <h2>{{ status.link?.username || t('sync.localOnly') }}</h2><p v-if="status.link">{{ status.link.server }}</p>
        <p>{{ t(status.enabled ? 'sync.enabled' : 'sync.paused') }}</p>
        <p role="status" aria-atomic="true">{{ t('sync.counts', { pending: Object.keys(status.pending).length, conflicts: Object.keys(status.conflicts).length }) }}</p>
        <p>{{ t('sync.last', { time: status.last_success ? new Date(status.last_success).toLocaleString(locale) : t('sync.never') }) }}</p>
        <p v-if="status.error" role="alert">{{ locale === 'zh' ? status.error : t('sync.requestFailed') }}</p>
        <div class="sync-actions">
          <button v-if="status.link" class="btn" :disabled="busy" @click="action(() => local.enable(!status.enabled))">{{ t(status.enabled ? 'sync.pause' : 'sync.enable') }}</button>
          <button v-if="status.enabled" class="btn ghost" :disabled="busy" @click="action(() => local.sync())">{{ t('sync.now') }}</button>
          <button v-if="status.link" class="btn ghost" :disabled="busy" @click="action(() => local.logout())">{{ t('sync.logout') }}</button>
        </div>
      </section>
      <section v-if="error" ref="errorSummary" class="card sync-error" role="alert" aria-labelledby="sync-errors-title" tabindex="-1">
        <h2 id="sync-errors-title">{{ t('sync.errorTitle') }}</h2><p>{{ message }}</p>
        <ul v-if="Object.keys(errors).length"><li v-for="(value,field) in errors" :key="field"><a :href="'#sync-' + field" @click.prevent="focusField(field)">{{ t('sync.' + field) }}: {{ value }}</a></li></ul>
      </section>
      <form ref="form" class="card" novalidate @submit.prevent="test">
        <h2>{{ t(status.link ? 'sync.relogin' : 'sync.login') }}</h2>
        <fieldset :disabled="busy">
          <label for="sync-server">{{ t('sync.server') }}</label><input id="sync-server" v-model="server" type="url" required placeholder="https://sub.example.com" autocomplete="url" :aria-invalid="!!errors.server" :aria-describedby="errors.server ? 'sync-server-error' : undefined" @input="clearCandidate('server')">
          <p v-if="errors.server" id="sync-server-error" class="field-error">{{ errors.server }}</p>
          <label for="sync-username">{{ t('sync.username') }}</label><input id="sync-username" v-model="username" required autocomplete="username" :aria-invalid="!!errors.username" :aria-describedby="errors.username ? 'sync-username-error' : undefined" @input="clearCandidate('username')">
          <p v-if="errors.username" id="sync-username-error" class="field-error">{{ errors.username }}</p>
          <label for="sync-password">{{ t('sync.password') }}</label><input id="sync-password" v-model="password" type="password" required autocomplete="current-password" :aria-invalid="!!errors.password" :aria-describedby="errors.password ? 'sync-password-error' : undefined" @input="clearCandidate('password')">
          <p v-if="errors.password" id="sync-password-error" class="field-error">{{ errors.password }}</p>
          <label for="sync-otp">{{ t('sync.otp') }}</label><input id="sync-otp" v-model="otp" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" :aria-invalid="!!errors.otp" :aria-describedby="errors.otp ? 'sync-otp-error' : undefined" @input="clearCandidate('otp')">
          <p v-if="errors.otp" id="sync-otp-error" class="field-error">{{ errors.otp }}</p>
          <p>{{ t('sync.loginHint') }}</p><button class="btn">{{ t(busy ? 'sync.working' : 'sync.test') }}</button>
        </fieldset>
        <p v-if="registration">{{ t('sync.registration') }} <a :href="registration" target="_blank" rel="noopener noreferrer">{{ t('sync.register') }}</a></p>
      </form>
      <p v-if="!error && message" role="status">{{ message }}</p><p v-if="busy" role="status">{{ t('sync.working') }}</p>
      <section v-if="candidate" ref="review" class="card" tabindex="-1">
        <h2>{{ t('sync.review') }}</h2><p>{{ candidate.server }} · {{ candidate.username }} · {{ t('sync.account', { id: candidate.account_id }) }}</p>
        <p>{{ t('sync.mergeCounts', { local: candidate.local_count, web: candidate.web_count ?? t('sync.unknown') }) }}</p><p>{{ t('sync.mergeHint') }}</p>
        <button class="btn" :disabled="busy" @click="connect">{{ t(busy ? 'sync.working' : 'sync.connect') }}</button>
      </section>
      <section v-for="(conflict,id) in status.conflicts" :key="id" class="card">
        <h2>{{ t('sync.conflict', { name: conflict.local.data.name || t('sync.title') }) }}</h2>
        <p v-if="conflict.error" role="alert">{{ locale === 'zh' ? conflict.error : t('sync.requestFailed') }} {{ t('sync.conflictHint') }}</p>
        <p v-if="conflict.local.kind === 'notification-config'">{{ t('sync.secretHint') }}</p>
        <details><summary>{{ t('sync.localVersion') }} {{ conflict.local.deleted ? t('sync.deleted') : '' }}</summary><pre>{{ JSON.stringify(conflict.local.data, null, 2) }}</pre></details>
        <details><summary>{{ t('sync.webVersion') }} {{ conflict.server?.deleted ? t('sync.deleted') : '' }}</summary><pre>{{ conflict.server ? JSON.stringify(conflict.server.data, null, 2) : t('sync.absent') }}</pre></details>
        <div class="sync-actions"><button class="btn" :disabled="busy" @click="action(() => local.resolve(id, 'local'))">{{ t('sync.keepLocal') }}</button><button class="btn ghost" :disabled="busy" @click="action(() => local.resolve(id, 'server'))">{{ t('sync.useWeb') }}</button></div>
      </section>
    </template>
  </div>
</template>
<script setup>
import { computed, inject, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createTransport, serverUrl } from './transport.js'
import { validateConnection } from './validation.js'
const { t, locale } = useI18n()
const local = inject('localSync'), revision = inject('previewRevision')
const status = computed(() => { revision.value; return local?.status })
const server = ref(status.value?.link?.server || ''), username = ref(status.value?.link?.username || ''), password = ref(''), otp = ref('')
const candidate = ref(null), registration = ref(''), message = ref(''), error = ref(false), busy = ref(false), errors = ref({})
const form = ref(null), errorSummary = ref(null), review = ref(null)
function focusField(field) { form.value?.querySelector('#sync-' + field)?.focus() }
function clearCandidate(field) { candidate.value = null; registration.value = ''; delete errors.value[field] }
async function showError() { await nextTick(); errorSummary.value?.focus() }
async function action(fn) {
  if (busy.value) return
  busy.value = true; error.value = false; message.value = ''
  try { await fn() }
  catch (e) {
    error.value = true
    message.value = e.code === 'SYNC_PROTOCOL_UNAVAILABLE' ? t('sync.serverUpgrade') : e.code === 'OTP_REQUIRED' ? t('sync.otpRequired') : e.code === 'ACCOUNT_NOT_REGISTERED' ? t('sync.registration') : e.status === 401 ? t('sync.loginFailed') : e.status === 403 ? t('sync.blocked') : locale.value === 'zh' ? e.message : t('sync.requestFailed')
    if (e.code === 'OTP_REQUIRED') errors.value.otp = message.value
    else if (e.code === 'ACCOUNT_NOT_REGISTERED') errors.value.username = message.value
    else if (e.status === 401) errors.value.password = message.value
    await showError()
  } finally { busy.value = false }
}
async function test() {
  if (busy.value) return
  candidate.value = null; registration.value = ''; errors.value = validateConnection({ server: server.value, username: username.value, password: password.value, otp: otp.value }, t)
  if (Object.keys(errors.value).length) { error.value = true; message.value = t('sync.errorTitle'); await showError(); return }
  await action(async () => {
    try { candidate.value = await local.test(server.value, username.value.trim(), password.value, otp.value); message.value = t('sync.verified'); await nextTick(); review.value?.focus() }
    catch (e) { if (e.code === 'ACCOUNT_NOT_REGISTERED') registration.value = createTransport(serverUrl(server.value), {}).registrationUrl; throw e }
    finally { password.value = ''; otp.value = '' }
  })
}
async function connect() { await action(async () => { await local.connect(candidate.value); candidate.value = null; message.value = t('sync.saved') }) }
</script>
<style scoped>
label { display: block; margin: 16px 0 8px; } input { width: 100%; min-height: 48px; box-sizing: border-box; } pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 280px; overflow: auto; } .card { overflow-wrap: anywhere; margin-bottom: 16px; } details { margin-block: 14px; } summary { min-height: 48px; cursor: pointer; } fieldset { border: 0; padding: 0; margin: 0; min-width: 0; } .sync-actions { display: flex; flex-wrap: wrap; gap: 12px; } .sync-error { border-color: var(--late); } .field-error { color: var(--late); margin: 8px 0; } [aria-invalid="true"] { border-color: var(--late); }
</style>
