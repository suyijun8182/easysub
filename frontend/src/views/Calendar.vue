<template>
  <div class="cal-page">
    <div class="page-head">
      <div>
        <h1 class="cal-title"><span>{{ monthName }}</span> <span class="cal-year">{{ year }}</span></h1>
        <p class="lede">{{ t('calendar.title') }}</p>
      </div>
      <div class="cal-nav">
        <button class="btn ghost icon" type="button" :aria-label="navLabel(-1)" :title="navLabel(-1)" @click="move(-1)">
          <span class="ico" v-html="icon('chevronL')"></span>
        </button>
        <button class="btn ghost" type="button" @click="goToday">{{ t('calendar.today') }}</button>
        <button class="btn ghost icon" type="button" :aria-label="navLabel(1)" :title="navLabel(1)" @click="move(1)">
          <span class="ico" v-html="icon('chevron')"></span>
        </button>
      </div>
    </div>

    <div class="card cal-card">
      <div class="cal">
        <div v-for="(d, i) in dows" :key="d" class="dow" :class="{ wknd: i === 0 || i === 6 }">{{ d }}</div>
        <button v-for="(cell, i) in cells" :key="cell.key" class="cell" type="button"
             :class="{ out: !cell.inMonth, today: cell.isToday, wknd: i % 7 === 0 || i % 7 === 6, sel: selected === cell.key }"
             :aria-label="dateLabel(cell)" :aria-pressed="selected === cell.key" :aria-current="cell.isToday ? 'date' : undefined"
             @click="select(cell)">
          <div class="dnum"><span class="num">{{ cell.day }}</span></div>
          <div class="evs">
            <div v-for="ev in cell.events.slice(0, 3)" :key="ev.id" class="ev" :class="statusOf(ev)" :title="ev.name">
              <SubIcon :icon="ev.icon" :name="ev.name" :size="16" />
              <span class="ev-name">{{ ev.name }}</span>
            </div>
            <span v-if="cell.events.length > 3" class="ev-more">
              {{ t('calendar.more', { n: cell.events.length - 3 }) }}
            </span>
          </div>
          <div v-if="cell.events.length" class="dots" aria-hidden="true">
            <span v-for="ev in cell.events.slice(0, 3)" :key="ev.id" class="dot" :class="statusOf(ev)"></span>
          </div>
        </button>
      </div>
    </div>

    <div class="card agenda" :class="{ pinned: selected }">
      <div class="ag-head">
        <h3>{{ agendaTitle }}</h3>
        <button v-if="selected" class="btn ghost sm icon" type="button" :aria-label="t('common.close')" @click="selected = null">
          <span class="ico" v-html="icon('x')"></span>
        </button>
      </div>
      <div v-if="agenda.length" class="ag-list">
        <component :is="androidPreview ? RouterLink : 'div'" v-for="ev in agenda" :key="ev.id + '-' + ev.next_renewal_date" class="ag-row" :to="androidPreview ? '/subscriptions/' + ev.id : undefined">
          <div class="ag-date num">
            <b>{{ dayOf(ev) }}</b>
            <span>{{ dowOf(ev) }}</span>
          </div>
          <SubIcon :icon="ev.icon" :name="ev.name" :size="32" />
          <div class="ag-main">
            <div class="ag-name">{{ ev.name }}<span v-if="ev.plan" class="ag-plan"> · {{ ev.plan }}</span></div>
            <div v-if="ev.remark" class="ag-remark">{{ ev.remark }}</div>
          </div>
          <div class="ag-side">
            <div v-if="ev.amount != null" class="ag-amt num">{{ Number(ev.amount).toFixed(2) }} {{ ev.currency }}</div>
            <span class="tag" :class="statusOf(ev)">{{ leftText(ev) }}</span>
          </div>
        </component>
      </div>
      <div v-else class="empty">
        <span class="empty-ico" v-html="icon('calendar')"></span>
        <div>{{ t(selected ? 'calendar.noEventsDay' : 'calendar.noEvents') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { icon } from '../icons'
import { daysLeft, statusOf } from '../lifeline'
import SubIcon from '../components/SubIcon.vue'

const { t, locale } = useI18n()
const androidPreview = inject('preview', null)
const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth())
const subs = ref([])
const selected = ref(null)   // 选中的日期 YYYY-MM-DD；为空时列表显示整月

const loc = computed(() => (locale.value === 'zh' ? 'zh-CN' : locale.value))
const pad = (n) => String(n).padStart(2, '0')
const keyOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const dateOf = (k) => new Date(k + 'T00:00:00')
const dueKey = (s) => String(s.next_renewal_date || '').slice(0, 10)
function dateLabel(cell) {
  const date = new Intl.DateTimeFormat(loc.value, { dateStyle: 'full' }).format(dateOf(cell.key))
  return androidPreview ? t('mobile.selectedDate', { date, count: cell.events.length }) : date + ' · ' + cell.events.length
}

const dows = computed(() => {
  const fmt = new Intl.DateTimeFormat(loc.value, { weekday: 'short' })
  // 2024-01-07 是周日
  return [...Array(7)].map((_, i) => fmt.format(new Date(2024, 0, 7 + i)))
})
const monthName = computed(() =>
  new Intl.DateTimeFormat(loc.value, { month: 'long' }).format(new Date(year.value, month.value, 1))
)
function navLabel(d) {
  return new Intl.DateTimeFormat(loc.value, { month: 'long', year: 'numeric' }).format(new Date(year.value, month.value + d, 1))
}

function move(d) {
  let m = month.value + d
  if (m < 0) { m = 11; year.value-- }
  else if (m > 11) { m = 0; year.value++ }
  month.value = m
  selected.value = null
}
function goToday() {
  const n = new Date()
  year.value = n.getFullYear(); month.value = n.getMonth()
  selected.value = null
}

// 按本地日期字符串比较，避免 new Date('YYYY-MM-DD') 的 UTC 偏移
function eventsOn(k) {
  return subs.value.filter((s) => s.next_renewal_date && s.show_in_calendar !== false && dueKey(s) === k)
}

const cells = computed(() => {
  const firstDow = new Date(year.value, month.value, 1).getDay()
  const todayKey = keyOf(new Date())
  const arr = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(year.value, month.value, 1 - firstDow + i)
    const key = keyOf(d)
    arr.push({ key, day: d.getDate(), inMonth: d.getMonth() === month.value, isToday: key === todayKey, events: eventsOn(key) })
  }
  // 若最后一整行都不属于本月则去掉（保持 5~6 行紧凑）
  if (arr.slice(35).every((c) => !c.inMonth)) return arr.slice(0, 35)
  return arr
})

function select(cell, force = false) {
  if (!force && selected.value === cell.key) { selected.value = null; return }
  if (!cell.inMonth) {
    const d = dateOf(cell.key)
    year.value = d.getFullYear(); month.value = d.getMonth()
  }
  selected.value = cell.key
}

const monthEvents = computed(() => {
  const prefix = `${year.value}-${pad(month.value + 1)}-`
  return subs.value
    .filter((s) => s.next_renewal_date && s.show_in_calendar !== false && dueKey(s).startsWith(prefix))
    .sort((a, b) => dueKey(a).localeCompare(dueKey(b)))
})
const agenda = computed(() => (selected.value ? eventsOn(selected.value) : monthEvents.value))
const agendaTitle = computed(() => {
  if (!selected.value) return `${monthName.value} ${year.value}`
  return new Intl.DateTimeFormat(loc.value, { month: 'long', day: 'numeric', weekday: 'long' }).format(dateOf(selected.value))
})

function dayOf(s) { return Number(dueKey(s).slice(8, 10)) }
function dowOf(s) { return new Intl.DateTimeFormat(loc.value, { weekday: 'short' }).format(dateOf(dueKey(s))) }
function leftText(s) {
  const d = daysLeft(s)
  if (d == null) return ''
  if (d === 0) return t('dashboard.today')
  if (d < 0) return t('dashboard.overdueDays', { n: -d })
  return t('dashboard.daysLeft', { n: d })
}

onMounted(async () => {
  const { data } = await api.get('/api/subscriptions', { params: { billing_type: 'recurring', active: true } })
  subs.value = data
})
</script>

<style scoped>
.ico { display: inline-flex; width: 18px; height: 18px; }
.ico :deep(svg) { width: 100%; height: 100%; }

.cal-title { font-variant-numeric: tabular-nums; }
.cal-year { color: var(--text-soft); font-weight: 450; }
.cal-nav { display: flex; align-items: center; gap: 6px; }

/* ---------- 月视图（仿 macOS 日历） ---------- */
.cal-card { padding: 0; overflow: hidden; }
.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.dow { text-align: right; font-size: 12px; font-weight: 550; color: var(--text-soft); padding: 10px 12px 8px; }
.dow.wknd { color: var(--text-faint); }
.cell { min-height: 112px; border: 0; background: var(--surface); color: var(--text); font: inherit; border-top: 1px solid var(--border); border-left: 1px solid var(--border);
  padding: 5px 6px 6px; display: flex; flex-direction: column; min-width: 0; cursor: pointer;
  transition: background-color .15s; outline: none; }
.cell:nth-child(7n + 1) { border-left: none; }
.cell.wknd { background: color-mix(in srgb, var(--surface-2) 45%, var(--surface)); }
.cell:hover { background: color-mix(in srgb, var(--surface-2) 75%, var(--surface)); }
.cell:focus-visible { box-shadow: inset 0 0 0 2px var(--primary); }
.cell.sel { background: var(--primary-soft); }
.num { font-variant-numeric: tabular-nums; }
.dnum { text-align: right; }
.dnum .num { display: inline-flex; align-items: center; justify-content: center; min-width: 26px; height: 26px;
  padding: 0 5px; border-radius: 999px; font-size: 13px; font-weight: 500; }
.cell.wknd .dnum .num { color: var(--text-soft); }
.cell.out .dnum .num { color: var(--text-faint); }
.cell.today .dnum .num { background: var(--primary); color: var(--on-primary); font-weight: 650; }

.evs { display: flex; flex-direction: column; gap: 3px; margin-top: 3px; min-width: 0; }
.ev { display: flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 550; line-height: 1.3;
  border-radius: 6px; padding: 2px 6px 2px 2px; min-width: 0; background: var(--surface-2); color: var(--text-soft); }
.ev.ok { background: var(--ok-soft); color: var(--ok); }
.ev.soon { background: var(--soon-soft); color: var(--soon); }
.ev.late { background: var(--late-soft); color: var(--late); }
.ev :deep(.sub-icon) { border-radius: 4px; }
.cell.out .ev { opacity: .55; }
.ev-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ev-more { align-self: flex-start; border: 0; background: none; padding: 1px 6px; font: inherit; font-size: 11.5px;
  font-weight: 550; color: var(--text-soft); cursor: pointer; border-radius: 5px; }
.ev-more:hover { color: var(--text); background: var(--surface-2); }
.dots { display: none; }

/* ---------- 日程列表：桌面端选中某天时显示，移动端常驻 ---------- */
.agenda { display: none; }
.agenda.pinned { display: block; margin-top: 16px; }
.ag-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 4px; min-height: 36px; }
.ag-head h3 { margin: 0; }
.ag-list { display: flex; flex-direction: column; }
.ag-row { display: flex; align-items: center; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--border); min-width: 0; }
.ag-row:last-child { border-bottom: none; }
.ag-date { width: 34px; flex-shrink: 0; display: flex; flex-direction: column; align-items: center; line-height: 1.15; }
.ag-date b { font-size: 17px; font-weight: 650; }
.ag-date span { font-size: 11px; color: var(--text-soft); }
.ag-main { flex: 1; min-width: 0; }
.ag-name { font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag-plan { font-weight: 500; color: var(--text-soft); }
.ag-remark { font-size: 12.5px; color: var(--text-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ag-side { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.ag-amt { font-size: 14px; font-weight: 600; }
.empty { padding: 28px 12px; }
.empty-ico { display: inline-flex; width: 32px; height: 32px; color: var(--text-faint); margin-bottom: 6px; }
.empty-ico :deep(svg) { width: 100%; height: 100%; margin: 0; }

/* ---------- 移动端：紧凑网格 + 状态圆点 + 日程列表 ---------- */
@media (max-width: 860px) {
  .cell { min-height: 58px; padding: 4px 2px 5px; align-items: center; }
  .dnum { text-align: center; }
  .evs { display: none; }
  .dots { display: flex; gap: 3px; margin-top: 4px; justify-content: center; }
  .dots .dot { width: 6px; height: 6px; }
  .dow { text-align: center; padding: 10px 2px 6px; }
  .agenda { display: block; margin-top: 14px; }
}
@media (max-width: 720px) {
  .cal-nav { width: 100%; }
  .cal-nav .btn:not(.icon) { flex: 1; }
  .cal-nav .btn.icon { width: 42px; }
  .cell { min-height: 52px; }
  .dnum .num { min-width: 30px; height: 30px; font-size: 14px; }
  .ag-row { gap: 10px; }
}
</style>
