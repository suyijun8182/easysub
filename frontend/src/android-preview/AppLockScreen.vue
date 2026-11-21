<script setup>
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
const props=defineProps({lock:{type:Object,required:true}})
const {t}=useI18n(), panel=ref(null)
watch(()=>props.lock.state.covered,async visible=>{if(visible){await nextTick();panel.value?.focus()}},{immediate:true})
function trap(event) {
  if(event.key!=='Tab')return
  const buttons=[...panel.value.querySelectorAll('button:not(:disabled)')]
  if(!buttons.length){event.preventDefault();return}
  const first=buttons[0],last=buttons.at(-1)
  if(event.shiftKey && (document.activeElement===first || document.activeElement===panel.value)){event.preventDefault();last.focus()}
  else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus()}
}
</script>
<template>
  <div v-if="lock.state.covered" ref="panel" class="android-preview app-lock-screen" role="dialog" aria-modal="true" aria-labelledby="app-lock-title" tabindex="-1" @keydown="trap">
    <section class="lock-card">
      <p>EasySub</p><h1 id="app-lock-title">{{ t('mobile.lockTitle') }}</h1>
      <p v-if="lock.state.booting || lock.state.authenticating" role="status">{{ t('mobile.lockChecking') }}</p>
      <p v-else-if="!lock.state.available">{{ t(lock.state.reason === 'NO_DEVICE_CREDENTIAL' ? 'mobile.lockRestoreDevice' : 'mobile.lockUnavailable') }}</p>
      <p v-else-if="lock.state.cancels >= 3">{{ t('mobile.lockAttempts') }}</p>
      <p v-else>{{ t('mobile.lockPrompt') }}</p>
      <p v-if="lock.state.error && lock.state.cancels < 3" role="alert">{{ t('mobile.lockError_' + lock.state.error) }}</p>
      <div class="actions">
        <button v-if="lock.state.available && lock.state.cancels < 3" type="button" class="btn" :disabled="lock.state.authenticating" @click="lock.unlock()">{{ t('mobile.lockUnlock') }}</button>
        <button type="button" class="btn ghost" @click="lock.exit()">{{ t('mobile.lockExit') }}</button>
      </div>
    </section>
  </div>
</template>
<style scoped>
.app-lock-screen { position:fixed; inset:0; z-index:20000; display:grid; place-items:center; padding:calc(24px + var(--app-inset-top)) 24px calc(24px + var(--app-inset-bottom)); background:var(--bg,#f6f7f5); color:var(--text,#16191d); }
.lock-card { width:100%; max-width:360px; }
h1 { font-size:24px; line-height:1.3; }
p { line-height:1.6; overflow-wrap:anywhere; }
.actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:24px; }
button { min-height:48px; }
</style>
