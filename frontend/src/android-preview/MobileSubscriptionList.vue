<script setup>
import { useI18n } from 'vue-i18n'
import SubIcon from '../components/SubIcon.vue'
import { daysLeft, statusOf } from '../lifeline.js'
defineProps({subscriptions:{type:Array,required:true}})
defineEmits(['renew','edit'])
const {t}=useI18n()
function dueText(s){const d=daysLeft(s);return d===null?t('sub.oneTime'):d<0?t('dashboard.overdueDays',{n:-d}):d===0?t('dashboard.today'):t('dashboard.daysLeft',{n:d})}
function cycleText(s){return s.billing_type==='one_time'?t('sub.oneTime'):`${s.cycle_count>1?s.cycle_count+' ':''}${t('sub.'+s.cycle)}`}
</script>
<template>
  <div class="app-subscription-list">
    <article v-for="s in subscriptions" :key="s.id" class="app-subscription" :class="'is-'+statusOf(s)">
      <div class="app-subscription-top"><router-link class="app-subscription-identity" :to="'/subscriptions/'+s.id"><SubIcon :icon="s.icon" :name="s.name" :size="32"/><span><strong>{{ s.name }}</strong><small>{{ s.remark || s.plan || s.next_renewal_date || t('sub.oneTime') }}</small></span></router-link><div class="app-subscription-amount"><strong>{{ Number(s.amount).toFixed(2) }} {{ s.currency }}</strong><small>/ {{ cycleText(s) }}</small></div></div>
      <div class="app-subscription-bottom"><span class="tag" :class="statusOf(s)">{{ dueText(s) }}</span><div class="app-subscription-actions"><button v-if="s.billing_type==='recurring'" class="btn ghost" @click="$emit('renew',s)">{{ t('sub.renew') }}</button><button class="btn ghost" @click="$emit('edit',s)">{{ t('sub.edit') }}</button></div></div>
    </article>
  </div>
</template>
<style scoped>
.app-subscription-list { display:grid; gap:var(--es-space-2); }
.app-subscription { border:var(--es-border-width) solid var(--border); border-radius:var(--es-radius-card); padding:var(--es-space-2); background:var(--surface); }
.app-subscription-top { display:flex; align-items:center; gap:var(--es-space-2); }
.app-subscription-identity { flex:1; min-width:0; display:flex; align-items:center; gap:var(--es-space-2); text-decoration:none; }
.app-subscription-identity > span { min-width:0; }.app-subscription-identity strong { display:block; font-size:var(--es-text-card); line-height:var(--es-leading-title); overflow-wrap:anywhere; }
.app-subscription small { display:block; font-size:var(--es-text-caption); color:var(--text-soft); overflow-wrap:anywhere; }
.app-subscription-amount { text-align:right; font-size:var(--es-text-label); font-variant-numeric:tabular-nums; }
.app-subscription-amount strong { white-space:nowrap; }
.app-subscription-bottom { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:var(--es-space-2); }
.app-subscription-actions { display:flex; gap:var(--es-space-2); }.app-subscription-actions .btn { padding-inline:var(--es-space-2); font-size:var(--es-text-label); white-space:nowrap; }
.app-subscription-bottom .tag { font-size:var(--es-text-caption); white-space:nowrap; }
</style>
