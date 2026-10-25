<template>
  <div class="dash">
    <header class="page-head">
      <div>
        <h1>{{ t('dashboard.greeting', { name: auth.user?.username || '' }) }}</h1>
        <p class="lede" v-if="!loading">
          <span v-if="lateList.length" class="sum late">{{ t('dashboard.summaryLate', { n: lateList.length }) }}</span>
          <span v-if="soonCount" class="sum soon">{{ t('dashboard.summarySoon', { n: soonCount }) }}</span>
          <span v-if="!lateList.length && !soonCount" class="sum ok">{{ t('dashboard.summaryClear') }}</span>
        </p>
      </div>
      <router-link to="/subscriptions" class="btn"><span v-html="icon('plus')"></span>{{ t('sub.add') }}</router-link>
    </header>

    <div v-if="loading" class="card skeleton" aria-busy="true"></div>
    <template v-else>
      <!-- 签名区：未来 30 天续费时间轴 -->
      <section class="card horizon" :aria-label="t('dashboard.nextDays', { n: horizon })">
        <div class="hz-head">
          <h3>{{ t('dashboard.nextDays', { n: horizon }) }}</h3>
          <router-link to="/calendar" class="more">{{ t('nav.calendar') }}<span v-html="icon('chevron')"></span></router-link>
        </div>

        <div class="hz-body">
          <div v-if="lateList.length" class="hz-late">
            <div class="hz-late-t">{{ t('dashboard.lateZone') }}</div>
            <div class="hz-late-items">
              <router-link v-for="s in lateList.slice(0, 6)" :key="s.id" to="/subscriptions" class="hz-chip late"
                           :title="chipTitle(s)" :aria-label="chipTitle(s)">
                <SubIcon :icon="s.icon" :name="s.name" :size="30" />
              </router-link>
              <span v-if="lateList.length > 6" class="hz-plus">+{{ lateList.length - 6 }}</span>
            </div>
          </div>

          <div class="hz-track" ref="trackEl" :style="{ height: trackHeight + 'px' }">
            <div class="hz-soon" :style="{ width: (7 / horizon * 100) + '%' }"></div>
            <div class="hz-axis"></div>
            <div v-for="tk in ticks" :key="tk.d" class="hz-tick" :style="{ left: tk.x + '%' }">
              <span>{{ tk.label }}</span>
            </div>
            <router-link v-for="(c, i) in placed" :key="c.s.id" to="/subscriptions" class="hz-chip" :class="c.st"
                         :style="{ left: c.x + '%', bottom: (34 + c.lane * 40) + 'px', '--d': i * 40 + 'ms' }"
                         :title="chipTitle(c.s)" :aria-label="chipTitle(c.s)">
              <SubIcon :icon="c.s.icon" :name="c.s.name" :size="30" />
              <span class="hz-stem" :style="{ height: (14 + c.lane * 40) + 'px' }"></span>
            </router-link>
            <p v-if="!placed.length" class="hz-empty muted">{{ t('dashboard.noneInDays', { n: horizon }) }}</p>
          </div>
        </div>
      </section>

      <!-- 支出概况：一条横向读数，而非四张同质卡片 -->
      <section class="card figures">
        <div class="fig">
          <span class="fig-l">{{ t('dashboard.monthSpend') }}</span>
          <span class="fig-v num">{{ money(data.month_spend) }}</span>
        </div>
        <div class="fig">
          <span class="fig-l">{{ t('dashboard.yearSpend') }}</span>
          <span class="fig-v num">{{ money(data.year_spend) }}</span>
        </div>
        <div class="fig">
          <span class="fig-l">{{ t('dashboard.active') }}</span>
          <span class="fig-v num">{{ data.active_count }}</span>
        </div>
        <div class="fig" :class="{ alarm: expiredCount > 0 }">
          <span class="fig-l">{{ t('dashboard.overdue') }}</span>
          <span class="fig-v num">{{ expiredCount }}</span>
        </div>
        <div v-if="data.monthly_budget" class="budget">
          <div class="bd-h">
            <span class="fig-l">{{ t('dashboard.budgetOf') }}</span>
            <span class="num" :class="{ over: overBudget }">{{ money(data.month_spend) }} / {{ money(data.monthly_budget) }}</span>
          </div>
          <div class="life" :class="overBudget ? 'late' : budgetPct >= 85 ? 'soon' : 'ok'">
            <i :style="{ transform: `scaleX(${budgetPct / 100})` }"></i>
          </div>
          <div class="bd-note muted">
            {{ overBudget ? t('remind.over') : t('remind.budgetLeft') }}：{{ money(Math.abs(data.monthly_budget - data.month_spend)) }}
          </div>
        </div>
      </section>

      <div class="split">
        <!-- 即将到期 -->
        <section class="card">
          <div class="sec-h">
            <h3>{{ t('dashboard.upcoming') }}</h3>
            <router-link to="/subscriptions" class="more">{{ t('dashboard.viewAll') }}<span v-html="icon('chevron')"></span></router-link>
          </div>
          <div v-if="!upcoming.length" class="empty sm"><span v-html="icon('check')"></span><p>{{ t('dashboard.none') }}</p></div>
          <ul class="due-list">
            <li v-for="(s, i) in upcoming" :key="s.id" class="due" :class="'is-' + statusOf(s)">
              <SubIcon :icon="s.icon" :name="s.name" :size="34" />
              <div class="due-main">
                <div class="due-top">
                  <span class="due-name">{{ s.name }}</span>
                  <span class="due-amt num">{{ amtText(s) }}</span>
                </div>
                <div class="due-meta">
                  <span class="due-when" :class="statusOf(s)">{{ dueText(s) }}</span>
                  <span class="muted num">{{ s.next_renewal_date }}</span>
                </div>
                <div v-bind="lifeAttrs(s, i)"><i :style="lifeBar(s).fill"></i></div>
              </div>
            </li>
          </ul>
        </section>

        <!-- 分类占比 -->
        <section class="card">
          <div class="sec-h">
            <h3>{{ t('dashboard.byCategory') }}</h3>
            <router-link to="/reports" class="more">{{ t('nav.reports') }}<span v-html="icon('chevron')"></span></router-link>
          </div>
          <div v-if="breakdown.length" class="donut-wrap">
            <div class="donut" :style="donutStyle" role="img" :aria-label="t('dashboard.byCategory')">
              <div class="donut-hole"><span class="num">{{ breakdown.length }}</span></div>
            </div>
            <ul class="legend">
              <li v-for="(b, i) in breakdown.slice(0, 7)" :key="b.category">
                <span class="sw" :style="{ background: color(i) }"></span>
                <span class="lg-n">{{ b.category }}</span>
                <span class="num muted">{{ b.percent }}%</span>
              </li>
            </ul>
          </div>
          <div v-else class="empty sm"><span v-html="icon('reports')"></span><p>{{ t('dashboard.none') }}</p></div>
        </section>
      </div>

      <!-- 分类总览：全部订阅，按到期排序 -->
      <section class="card" v-if="catGroups.length">
        <h3>{{ t('dashboard.catOverview') }}</h3>
        <div class="cat-cols">
          <div v-for="g in catGroups" :key="g.key" class="cat-col">
            <div class="cc-head">
              <span class="cc-name"><span class="cc-ico" v-if="g.icon">{{ g.icon }}</span>{{ g.name }}</span>
              <span class="tag num">{{ g.items.length }}</span>
            </div>
            <router-link v-for="s in g.items" :key="s.id" to="/subscriptions" class="cc-item">
              <span class="dot" :class="statusOf(s)"></span>
              <SubIcon :icon="s.icon" :name="s.name" :size="22" />
              <span class="cc-n">{{ s.name }}</span>
              <span class="cc-d num" :class="statusOf(s)">{{ s.next_renewal_date ? dueShort(s) : t('dashboard.oneTimeShort') }}</span>
            </router-link>
          </div>
        </div>
      </section>

      <!-- 最近添加 -->
      <section class="card" v-if="data.recent.length">
        <h3>{{ t('dashboard.recent') }}</h3>
        <div class="recent">
          <div v-for="s in data.recent" :key="s.id" class="rc">
            <SubIcon :icon="s.icon" :name="s.name" :size="32" />
            <div class="rc-main">
              <div class="rc-n">{{ s.name }}</div>
              <div class="muted num rc-a">{{ money(s.amount_in_base) }}</div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'
import { daysLeft, lifeBar, statusOf } from '../lifeline'
import SubIcon from '../components/SubIcon.vue'

const { t } = useI18n()
const auth = useAuth()
const loading = ref(true)
const data = ref({ upcoming: [], recent: [] })
const breakdown = ref([])
const expiredCount = ref(0)
const allSubs = ref([])
const cats = ref([])

const overBudget = computed(() => data.value.monthly_budget && data.value.month_spend > data.value.monthly_budget)
const budgetPct = computed(() => {
  const b = data.value.monthly_budget
  if (!b) return 0
  return Math.min(100, Math.round((data.value.month_spend / b) * 100))
})

// 分类用色：刻意避开状态色（绿/黄/红只表示到期状态）
const PALETTE = ['#3b6fd8', '#7a5af8', '#0e9aa7', '#c0408f', '#5b6b7f', '#3aa0e0', '#8a6d3b', '#9b7be0']
function color(i) { return PALETTE[i % PALETTE.length] }

function money(v) {
  const cur = auth.user?.base_currency || 'CNY'
  return `${cur} ${Number(v || 0).toFixed(2)}`
}
function dueText(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  if (d < 0) return t('dashboard.overdueDays', { n: -d })
  return d === 0 ? t('dashboard.today') : t('dashboard.daysLeft', { n: d })
}
function dueShort(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  return d < 0 ? t('dashboard.overdueDays', { n: -d }) : d === 0 ? t('dashboard.today') : `${d}d`
}
// 订阅列表接口不一定带折算金额，缺失时显示原币金额
function amtText(s) {
  if (s.amount_in_base != null) return money(s.amount_in_base)
  return `${s.currency || ''} ${Number(s.amount || 0).toFixed(2)}`
}
function chipTitle(s) { return `${s.name} · ${s.next_renewal_date} · ${dueText(s)}` }
function lifeAttrs(s, i) {
  const b = lifeBar(s, i)
  return { class: b.cls, style: b.style }
}

const recurring = computed(() => allSubs.value.filter((s) => s.billing_type === 'recurring' && s.next_renewal_date))
const lateList = computed(() => recurring.value.filter((s) => daysLeft(s) < 0).sort((a, b) => daysLeft(a) - daysLeft(b)))
const soonCount = computed(() => recurring.value.filter((s) => statusOf(s) === 'soon').length)

// 「即将到期」列表优先用完整订阅数据（含周期，周期条才能算），缺失时退回接口数据
const upcoming = computed(() => {
  const byId = new Map(allSubs.value.map((s) => [s.id, s]))
  const api = (data.value.upcoming || []).map((u) => ({ ...(byId.get(u.id) || {}), ...u }))
  if (api.length) return api
  return recurring.value.filter((s) => daysLeft(s) >= 0).sort((a, b) => daysLeft(a) - daysLeft(b)).slice(0, 5)
})
// 时间轴范围自适应：30 / 60 / 90 天里取最小的、能放下至少 3 项的
const horizon = computed(() => {
  const ds = recurring.value.map(daysLeft).filter((d) => d >= 0)
  for (const h of [30, 60, 90]) if (ds.filter((d) => d <= h).length >= Math.min(3, ds.length)) return h
  return 90
})

/* ---------- 30 天时间轴：按到期日定位，重叠时分层 ---------- */
const trackEl = ref(null)
const trackW = ref(800)
function measure() { if (trackEl.value) trackW.value = trackEl.value.clientWidth || 800 }
const placed = computed(() => {
  const items = recurring.value
    .map((s) => ({ s, d: daysLeft(s) }))
    .filter((x) => x.d >= 0 && x.d <= horizon.value)
    .sort((a, b) => a.d - b.d)
  const gap = 36 / Math.max(trackW.value, 1) * 100   // 图标宽度换算成百分比
  const lanes = []
  return items.map(({ s, d }) => {
    const x = Math.min(100, (d / horizon.value) * 100)
    let lane = lanes.findIndex((last) => x - last >= gap)
    if (lane === -1) {
      if (lanes.length < 4) lane = lanes.length
      else lane = lanes.indexOf(Math.min(...lanes))
    }
    lanes[lane] = x
    return { s, x, lane, st: statusOf(s) }
  })
})
const trackHeight = computed(() => {
  const maxLane = placed.value.reduce((m, c) => Math.max(m, c.lane), 0)
  return 34 + (maxLane + 1) * 40 + 12
})
const ticks = computed(() => {
  const out = []
  const h = horizon.value
  for (const d of [0, h / 4, h / 2, (h * 3) / 4, h].map(Math.round)) {
    const dt = new Date()
    dt.setDate(dt.getDate() + d)
    out.push({ d, x: (d / h) * 100, label: d === 0 ? t('calendar.today') : `${dt.getMonth() + 1}/${dt.getDate()}` })
  }
  return out
})

const catGroups = computed(() => {
  const byCat = {}
  for (const s of allSubs.value) {
    const key = s.category_id == null ? 'none' : String(s.category_id)
    ;(byCat[key] ||= []).push(s)
  }
  const order = Object.keys(byCat).sort((a, b) => {
    if (a === 'none') return 1
    if (b === 'none') return -1
    return 0
  })
  return order.map((key) => {
    const c = cats.value.find((x) => String(x.id) === key)
    // 按到期时间排序：越早到期越靠前；一次性买断/无到期日排最后
    const items = byCat[key].slice().sort((a, b) => {
      const da = daysLeft(a)
      const db = daysLeft(b)
      if (da === null && db === null) return 0
      if (da === null) return 1
      if (db === null) return -1
      return da - db
    })
    return {
      key,
      icon: key === 'none' ? '' : (c?.icon || ''),
      name: key === 'none' ? t('sub.uncategorized') : (c?.name || key),
      items
    }
  })
})

const donutStyle = computed(() => {
  if (!breakdown.value.length) return { background: 'var(--border)' }
  let acc = 0
  const stops = []
  breakdown.value.forEach((b, i) => {
    const start = acc; acc += b.percent
    stops.push(`${color(i)} ${start}% ${acc}%`)
  })
  if (acc < 100) stops.push(`var(--surface-2) ${acc}% 100%`)
  return { background: `conic-gradient(${stops.join(',')})` }
})

onMounted(async () => {
  window.addEventListener('resize', measure)
  const [d, ins, exp, subs, c] = await Promise.all([
    api.get('/api/dashboard'),
    api.get('/api/reports/insights').catch(() => ({ data: { breakdown: [] } })),
    api.get('/api/reports/expired').catch(() => ({ data: [] })),
    api.get('/api/subscriptions', { params: { active: true } }).catch(() => ({ data: [] })),
    api.get('/api/categories').catch(() => ({ data: [] }))
  ])
  data.value = d.data
  breakdown.value = ins.data.breakdown || []
  expiredCount.value = (exp.data || []).length
  allSubs.value = subs.data || []
  cats.value = c.data || []
  loading.value = false
  nextTick(measure)
})
onBeforeUnmount(() => window.removeEventListener('resize', measure))
</script>

<style scoped>
.lede { display: flex; flex-wrap: wrap; gap: 6px 14px; margin-top: 6px !important; }
.sum { display: inline-flex; align-items: center; gap: 7px; font-weight: 550; }
.sum::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.sum.late { color: var(--late); }
.sum.soon { color: var(--soon); }
.sum.ok { color: var(--ok); }
.page-head .btn span { display: inline-flex; }

.skeleton { height: 220px; background: linear-gradient(90deg, var(--surface) 30%, var(--surface-2) 50%, var(--surface) 70%);
  background-size: 300% 100%; animation: shimmer 1.4s linear infinite; }
@keyframes shimmer { from { background-position: 100% 0; } to { background-position: 0 0; } }

.more { display: inline-flex; align-items: center; gap: 2px; font-size: 13px; color: var(--text-soft); text-decoration: none; }
.more:hover { color: var(--text); }
.more span { width: 14px; height: 14px; display: inline-flex; }

/* ---------- 时间轴 ---------- */
.horizon { padding: 20px 22px 14px; }
.hz-head { display: flex; justify-content: space-between; align-items: baseline; }
.hz-head h3 { margin: 0; }
.hz-body { display: flex; gap: 18px; align-items: stretch; margin-top: 10px; }
.hz-late { flex-shrink: 0; width: 92px; padding: 10px; border-radius: var(--radius-sm); background: var(--late-soft);
  display: flex; flex-direction: column; gap: 8px; align-self: flex-end; margin-bottom: 26px; }
.hz-late-t { font-size: 12px; font-weight: 600; color: var(--late); }
.hz-late-items { display: flex; flex-wrap: wrap; gap: 6px; }
.hz-plus { font-size: 12px; color: var(--late); align-self: center; }
.hz-track { position: relative; flex: 1; min-width: 0; margin: 0 16px 0 16px; transition: height .3s var(--ease-out); }
.hz-axis { position: absolute; left: 0; right: 0; bottom: 26px; height: 2px; border-radius: 1px; background: var(--border-strong); }
.hz-soon { position: absolute; left: 0; bottom: 22px; height: 10px; border-radius: 5px;
  background: color-mix(in srgb, var(--soon-bar) 22%, transparent); }
.hz-tick { position: absolute; bottom: 0; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.hz-tick::before { content: ''; width: 1px; height: 8px; background: var(--border-strong); margin-bottom: 4px; }
.hz-tick span { font-size: 11.5px; color: var(--text-soft); font-variant-numeric: tabular-nums; white-space: nowrap; }
.hz-chip { position: absolute; transform: translateX(-50%); display: inline-flex; border-radius: 10px; text-decoration: none;
  animation: chip-in .6s var(--ease-out) both; animation-delay: var(--d, 0ms); transition: transform .2s var(--ease-out); z-index: 1; }
.hz-late .hz-chip { position: static; transform: none; animation: none; }
.hz-chip :deep(.sub-icon) { box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--ok-bar), var(--shadow); }
.hz-chip.soon :deep(.sub-icon) { box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--soon-bar), var(--shadow); }
.hz-chip.late :deep(.sub-icon) { box-shadow: 0 0 0 2px var(--late-soft), 0 0 0 4px var(--late-bar); }
.hz-chip:hover { transform: translateX(-50%) translateY(-3px); z-index: 2; }
.hz-late .hz-chip:hover { transform: translateY(-2px); }
.hz-stem { position: absolute; left: 50%; top: 100%; width: 1px; background: var(--border-strong); pointer-events: none; }
.hz-empty { position: absolute; left: 0; right: 0; bottom: 40px; text-align: center; margin: 0; font-size: 14px; }
@keyframes chip-in { from { opacity: 0; translate: 0 10px; } }

/* ---------- 读数条 ---------- */
.figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; padding: 0; }
.fig { padding: 18px 20px; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.fig + .fig { border-left: 1px solid var(--border); }
.fig-l { font-size: 13px; color: var(--text-soft); }
.fig-v { font-size: 24px; font-weight: 650; letter-spacing: -.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fig.alarm .fig-v { color: var(--late); }
.budget { grid-column: 1 / -1; border-top: 1px solid var(--border); padding: 14px 20px 16px; }
.bd-h { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; margin-bottom: 8px; }
.bd-h .over { color: var(--late); font-weight: 600; }
.bd-note { font-size: 12.5px; margin-top: 6px; }

/* ---------- 双栏 ---------- */
.split > * { min-width: 0; }
.split { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 16px; margin-top: 16px; }
.split > .card + .card { margin-top: 0; }
.split + .card { margin-top: 16px; }
.sec-h { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.sec-h h3 { margin: 0; }

.due-list { list-style: none; margin: 0; padding: 0; }
.due { display: flex; gap: 12px; align-items: center; padding: 11px 0; border-bottom: 1px solid var(--border); }
.due:last-child { border-bottom: 0; padding-bottom: 2px; }
.due-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.due-top, .due-meta { display: flex; justify-content: space-between; gap: 10px; align-items: baseline; }
.due-name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.due-amt { font-weight: 600; white-space: nowrap; }
.due-meta { font-size: 12.5px; }
.due-when { font-weight: 600; color: var(--ok); }
.due-when.soon { color: var(--soon); }
.due-when.late { color: var(--late); }
.due .life { height: 4px; margin-top: 2px; }

.empty.sm { padding: 20px 10px; }
.empty.sm span { display: inline-flex; width: 28px; height: 28px; color: var(--text-faint); }
.empty.sm p { margin: 6px 0 0; font-size: 14px; }

.donut-wrap { display: flex; align-items: center; gap: 22px; margin-top: 12px; }
.donut { width: 132px; height: 132px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.donut-hole { width: 84px; height: 84px; border-radius: 50%; background: var(--surface); display: flex; align-items: center;
  justify-content: center; font-size: 22px; font-weight: 650; }
.legend { list-style: none; margin: 0; padding: 0; flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.legend li { display: flex; align-items: center; gap: 9px; font-size: 13.5px; }
.sw { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.lg-n { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ---------- 分类总览 ---------- */
.cat-cols { align-items: start; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px; }
.cat-col { border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px 10px 6px; background: color-mix(in srgb, var(--surface-2) 35%, var(--surface)); }
.cc-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 2px 4px 8px; font-weight: 600; font-size: 14px; }
.cc-name { display: flex; align-items: center; gap: 6px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cc-item { display: flex; align-items: center; gap: 8px; padding: 6px 4px; min-height: 36px; border-radius: 8px;
  font-size: 13.5px; color: var(--text); text-decoration: none; transition: background-color .12s; }
.cc-item:hover { background: var(--surface); }
.cc-n { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cc-d { font-size: 12px; color: var(--text-soft); white-space: nowrap; }
.cc-d.soon { color: var(--soon); font-weight: 600; }
.cc-d.late { color: var(--late); font-weight: 600; }

.recent { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
.rc { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: var(--radius-sm); background: var(--surface-2); }
.rc-main { min-width: 0; }
.rc-n { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rc-a { font-size: 12.5px; }

.figures, .card.horizon + .figures { margin-top: 16px; }

@media (max-width: 1000px) {
  .split { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 720px) {
  .horizon { padding: 16px 14px 10px; }
  .hz-body { flex-direction: column; gap: 10px; }
  .hz-late { width: auto; align-self: stretch; flex-direction: row; align-items: center; margin-bottom: 0; }
  .hz-track { flex: none; margin: 0 20px; }
  .figures { grid-template-columns: 1fr 1fr; }
  .fig { padding: 14px 16px; }
  .fig:nth-child(3) { border-left: 0; }
  .fig:nth-child(n+3) { border-top: 1px solid var(--border); }
  .fig-v { font-size: 20px; }
  .budget { padding: 12px 16px 14px; }
  .donut { width: 112px; height: 112px; }
  .donut-hole { width: 70px; height: 70px; }
}
</style>
