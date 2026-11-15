<script setup>
import { computed, onMounted, onBeforeUnmount, shallowRef, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import SubIcon from '../components/SubIcon.vue'
import { groupRenewalDates, placeRenewalDates, timelineLabel } from './timeline-layout.js'
const props=defineProps({ subscriptions:{type:Array,required:true} })
const {t}=useI18n(), track=ref(null), sheet=ref(null), width=shallowRef(260), selected=shallowRef(null)
const today=new Date(), todayKey=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`
const placed=computed(()=>placeRenewalDates(groupRenewalDates(props.subscriptions,todayKey),width.value))
const lanes=computed(()=>Math.max(1,...placed.value.map(g=>g.lane+1)))
let observer
onMounted(()=>{observer=new ResizeObserver(()=>{width.value=track.value.clientWidth});observer.observe(track.value)})
onBeforeUnmount(()=>observer?.disconnect())
function select(group){selected.value=group;sheet.value.showModal()}
</script>
<template>
  <section class="app-timeline card" :aria-label="t('dashboard.nextDays',{n:30})">
    <div class="app-timeline-heading"><h2>{{ t('dashboard.nextDays',{n:30}) }}</h2><router-link to="/calendar">{{ t('nav.calendar') }}</router-link></div>
    <div ref="track" class="app-timeline-track" :style="{'--lanes':lanes}">
      <span class="app-today">{{ t('dashboard.today') }}</span>
      <button v-for="group in placed" :key="group.date" class="app-timeline-mark" :style="{left:group.x+'px','--lane':group.lane}" :aria-label="timelineLabel(group)" @click="select(group)"><SubIcon :icon="group.items[0].icon" :name="group.items[0].name" :size="32"/><span v-if="group.items.length>1" class="app-timeline-count">+{{ group.items.length-1 }}</span></button>
      <p v-if="!placed.length" class="muted">{{ t('dashboard.noneInDays',{n:30}) }}</p>
    </div>
    <dialog ref="sheet" class="app-date-sheet" :aria-label="selected?.date"><header><h2>{{ selected?.date }}</h2><button class="btn ghost" @click="sheet.close()">{{ t('common.close') }}</button></header><ul><li v-for="s in selected?.items" :key="s.id"><router-link :to="'/subscriptions/'+s.id" @click="sheet.close()"><strong>{{ s.name }}</strong><span>{{ s.remark || s.plan }}</span><span>{{ s.next_renewal_date }} · {{ Number(s.amount).toFixed(2) }} {{ s.currency }}</span></router-link></li></ul></dialog>
  </section>
</template>
<style scoped>
.app-timeline-heading,.app-date-sheet header { display:flex; align-items:center; justify-content:space-between; gap:var(--es-space-2); }
.app-timeline h2 { margin:0; font-size:var(--es-text-section); }
.app-timeline-heading a { font-size:var(--es-text-caption); }
/* Positions are measured timeline geometry; 48 is the minimum touch/clearance grid. */
.app-timeline-track { position:relative; min-height:calc(var(--lanes)*var(--es-control-min) + var(--es-space-8)); margin-top:var(--es-space-4); border-bottom:var(--es-border-width) solid var(--border-strong); }
.app-today { position:absolute; left:0; top:0; height:100%; border-left:var(--es-focus-width) solid var(--text); padding-left:var(--es-space-1); font-size:var(--es-text-caption); }
.app-timeline-mark { position:absolute; top:calc(var(--lane)*var(--es-control-min) + var(--es-space-6)); transform:translateX(-50%); display:grid; place-items:center; padding:0; min-width:var(--es-control-min); background:none; border:0; color:var(--text); }
.app-timeline-count { position:absolute; top:0; right:0; padding:0 var(--es-space-1); background:var(--primary); color:var(--on-primary); border-radius:var(--es-radius-round); font-size:var(--es-text-caption); }
.app-date-sheet { width:min(100%,var(--es-content-max)); max-height:80dvh; margin:auto auto 0; padding:var(--es-space-4); border:var(--es-border-width) solid var(--border); border-radius:var(--es-radius-sheet) var(--es-radius-sheet) 0 0; color:var(--text); background:var(--surface); }
.app-date-sheet ul { list-style:none; padding:0; }.app-date-sheet a { display:grid; gap:var(--es-space-1); padding-block:var(--es-space-3); }.app-date-sheet span { font-size:var(--es-text-label); }
</style>
