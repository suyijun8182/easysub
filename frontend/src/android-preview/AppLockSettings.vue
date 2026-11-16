<script setup>
import { inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const lock=inject('appLock'), {t}=useI18n()
onMounted(()=>lock.refresh())
async function changeEnabled(event) {
  const enabled=event.target.checked;event.target.checked=lock.state.enabled
  await lock.configure(enabled,lock.state.relockMinutes)
}
async function changeMinutes(event) {
  const minutes=Number(event.target.value);event.target.value=String(lock.state.relockMinutes)
  await lock.configure(true,minutes)
}
</script>
<template>
  <section class="card app-lock-settings" :aria-busy="lock.state.busy">
    <h2>{{ t('mobile.lockTitle') }}</h2>
    <p v-if="lock.state.reason === 'PREVIEW'">{{ t('mobile.lockPreview') }}</p>
    <p v-else-if="!lock.state.available">{{ t(lock.state.reason === 'NO_DEVICE_CREDENTIAL' ? 'mobile.lockNoDevice' : 'mobile.lockUnavailable') }}</p>
    <p v-else>{{ t(lock.state.enabled ? 'mobile.lockEnabled' : 'mobile.lockDisabled') }}</p>
    <label class="check-label"><input type="checkbox" :checked="lock.state.enabled" :disabled="!lock.state.available || lock.state.busy" @change="changeEnabled">{{ t('mobile.lockToggle') }}</label>
    <label>{{ t('mobile.lockRelock') }}<select :value="lock.state.relockMinutes" :disabled="!lock.state.enabled || lock.state.busy" @change="changeMinutes"><option v-for="minutes in [0,1,5,15]" :key="minutes" :value="minutes">{{ minutes === 0 ? t('mobile.lockImmediately') : t('mobile.lockMinutes',{n:minutes}) }}</option></select></label>
    <p class="muted">{{ t('mobile.lockPrivacyHint') }}</p>
    <p v-if="lock.state.settingsError" class="err" role="alert">{{ t('mobile.lockError_' + lock.state.settingsError) }}</p>
  </section>
</template>
