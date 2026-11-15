<template>
  <div>
    <header class="page-head"><h1>{{ t('mobile.detail') }}</h1><button class="btn ghost" @click="goBack">{{ t('mobile.backPage') }}</button></header>
    <template v-if="subscription">
      <section class="card detail-summary"><SubIcon :icon="subscription.icon" :name="subscription.name" :size="56"/><div><h2>{{ subscription.name }}</h2><p v-if="subscription.plan">{{ subscription.plan }}</p><strong class="detail-amount num">{{ subscription.amount.toFixed(2) }} {{ subscription.currency }}</strong><p>{{ subscription.next_renewal_date || t('sub.oneTime') }}</p></div></section>
      <section class="card"><dl class="detail-fields"><div v-for="field in fields" :key="field.key"><dt>{{ field.label }}</dt><dd>{{ field.value }}</dd></div></dl></section>
      <section v-if="progress !== null" class="card app-cycle-progress"><p>{{ t('mobile.cycleElapsed',{n:progress}) }}</p><div role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100" :aria-label="t('mobile.cycleElapsed',{n:progress})" class="life"><i :style="{transform:`scaleX(${progress/100})`}"></i></div></section>
      <section v-if="subscription.remark || subscription.notes" class="card"><h2>{{ t('sub.notes') }}</h2><p class="detail-notes">{{ subscription.remark }}</p><p class="detail-notes">{{ subscription.notes }}</p></section>
      <div class="detail-actions"><router-link v-if="subscription.billing_type === 'recurring'" class="btn" :to="{path:'/subscriptions',query:{renew:subscription.id}}">{{ t('sub.renew') }}</router-link><router-link class="btn ghost" :to="{path:'/subscriptions',query:{edit:subscription.id}}">{{ t('sub.edit') }}</router-link></div>
      <section class="card app-danger-zone"><h2>{{ t('sub.delete') }}</h2><router-link class="btn danger" :to="{path:'/subscriptions',query:{delete:subscription.id}}">{{ t('sub.delete') }}</router-link></section>
    </template><p v-else role="status">{{ t('reports.noData') }}</p>
  </div>
</template>
<script setup>
import { computed, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SubIcon from '../components/SubIcon.vue'
import { detailBackTarget } from './ui-behavior.js'
import { billingProgress } from './billing-progress.js'
import { paymentName } from './display-names.js'
const route = useRoute(), router = useRouter(), preview = inject('preview'), { t, locale } = useI18n()
const revision = inject('previewRevision')
function goBack() {
  const state = router.options.history.state
  if (state?.back && detailBackTarget(state) === state.back) router.back()
  else router.replace('/subscriptions')
}
const subscription = computed(() => { revision.value; return preview.state.subscriptions.find(s => s.id === Number(route.params.id)) })
const progress = computed(() => { revision.value; return subscription.value ? billingProgress(subscription.value) : null })
const fields = computed(() => {
  revision.value
  const s = subscription.value
  if (!s) return []
  const category = preview.state.categories.find(c=>c.id===s.category_id)?.name
  const payment = paymentName(preview.state.payment_methods.find(c=>c.id===s.payment_method_id),locale.value)
  const bundle = preview.state.bundles.find(c=>c.id===s.bundle_id)?.name
  const entries = [
    ['category',t('sub.category'),category],['payment',t('sub.payment'),payment],['bundle',t('mobile.bundles'),bundle],
    ['start',t('sub.startDate'),s.start_date],['end',t('sub.endDate'),s.end_date],['cycle',t('sub.cycle'),`${s.cycle_count} ${t('sub.' + s.cycle)}`],
    ['remind',t('sub.remindDays'),s.remind_days_before],['trial',t('sub.trialEnd'),s.trial_end],['cancel',t('sub.cancelBy'),s.cancel_by],
    ['card',t('sub.cardLast4'),s.card_last4],['expiry',t('sub.cardExpiry'),s.card_expiry],
    ['ipv4','IPv4',s.ipv4],['ipv6','IPv6',s.ipv6],['family',t('sub.family'),(s.family_members||[]).join('、')],['url','URL',s.url]
    ,['auto-renew',t('sub.autoRenew'),s.auto_renew ? '✓' : '—']
  ]
  return entries.filter(e=>e[2]).map(([key,label,value])=>({key,label,value}))
})
</script>
