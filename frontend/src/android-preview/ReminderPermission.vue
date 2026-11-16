<template>
  <section class="app-notification-permission" aria-live="polite">
    <h2>{{ t('mobile.notifTitle') }}</h2>
    <p>{{ t('mobile.notif_' + reminders.state.permission) }}</p>
    <p class="muted">{{ t('mobile.notifHint') }}</p>
    <div v-if="reminders.state.permission === 'denied'" class="actions">
      <button v-if="reminders.state.required" class="btn" type="button" @click="request">{{ t('mobile.notifRequest') }}</button>
      <button class="btn ghost" type="button" @click="openSettings">{{ t('mobile.notifSettings') }}</button>
    </div>
    <p v-if="reminders.state.error" class="err" role="alert">{{ t('mobile.notifError') }}</p>
  </section>
</template>
<script setup>
import { inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const {t}=useI18n(), reminders=inject('reminders')
const request=()=>reminders.requestPermission()
async function openSettings() {try{await reminders.openSettings()}catch{reminders.state.error=true}}
onMounted(()=>reminders.refresh())
</script>
