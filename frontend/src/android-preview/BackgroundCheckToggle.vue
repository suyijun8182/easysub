<script setup>
import { inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
const check = inject('backgroundCheck'), { t } = useI18n()
onMounted(() => check.refresh())
</script>
<template>
  <section class="card background-check" :aria-busy="check.state.busy">
    <h2>{{ t('sync.backgroundTitle') }}</h2>
    <label class="check-label"><input type="checkbox" :checked="check.state.enabled" :disabled="!check.state.available || check.state.busy" @change="check.setEnabled($event.target.checked)">{{ t('sync.backgroundToggle') }}</label>
    <p class="muted">{{ t('sync.backgroundHint') }}</p>
    <p v-if="check.state.error" class="err" role="alert">{{ t('sync.backgroundError') }}</p>
  </section>
</template>
