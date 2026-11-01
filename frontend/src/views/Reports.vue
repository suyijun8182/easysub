<template>
  <div class="rep-page">
    <div class="page-head">
      <div>
        <h1>{{ t('reports.title') }}</h1>
      </div>
      <button class="btn ghost" type="button" @click="exportCsv">
        <span class="ico" v-html="icon('download')"></span>{{ t('reports.exportCsv') }}
      </button>
    </div>

    <div class="tabs-scroll">
      <div class="seg" role="tablist">
        <button v-for="tab in tabs" :key="tab" type="button" role="tab" :aria-selected="active === tab"
                :class="{ on: active === tab }" @click="active = tab">
          {{ t('reports.' + tab) }}
        </button>
      </div>
    </div>

    <!-- 总览（图表） -->
    <div v-if="active === 'overview'">
      <div class="card stats">
        <div class="stat">
          <div class="stat-l">{{ t('reports.monthlyTotal') }}</div>
          <div class="stat-v num"><small>{{ cur }}</small> {{ (insights.monthly_total || 0).toFixed(2) }}</div>
        </div>
        <div class="stat">
          <div class="stat-l">{{ t('reports.yearlyTotal') }}</div>
          <div class="stat-v num"><small>{{ cur }}</small> {{ ((insights.monthly_total || 0) * 12).toFixed(2) }}</div>
        </div>
        <div class="stat">
          <div class="stat-l">{{ t('reports.recurringSubs') }}</div>
          <div class="stat-v num">{{ recurringCount }}</div>
        </div>
        <div class="stat">
          <div class="stat-l">{{ t('reports.permanentTotal') }}</div>
          <div class="stat-v num"><small>{{ cur }}</small> {{ (detail.one_time_total || 0).toFixed(2) }}</div>
        </div>
      </div>

      <div class="grid two">
        <div class="card">
          <h3>{{ t('reports.byCategory') }}</h3>
          <div v-if="segments.length" class="donut-wrap">
            <div v-if="!androidPreview || segments.length <= 4" class="donut" :style="donutStyle" role="img" :aria-label="t('reports.byCategory')">
              <div class="donut-hole">
                <div class="dh-v num">{{ (insights.monthly_total || 0).toFixed(0) }}</div>
                <div class="dh-l">{{ cur }} {{ t('reports.monthly') }}</div>
              </div>
            </div>
            <div v-if="!androidPreview || segments.length <= 4" class="legend">
              <div v-for="(b, i) in insights.breakdown" :key="b.category" class="lg">
                <span class="sw" :style="{ background: color(i) }"></span>
                <span class="lg-n">{{ b.category }}</span>
                <span class="lg-p num">{{ b.percent }}%</span>
              </div>
            </div>
            <div v-else class="ranked-categories">
              <div v-for="b in insights.breakdown" :key="b.category"><div class="category-line"><span>{{ b.category }}</span><span class="category-value">{{ cur }} {{ b.monthly.toFixed(2) }} · {{ b.percent }}%</span></div><div class="category-track"><i :style="{ width: barW(b) + '%' }"></i></div></div>
            </div>
          </div>
          <div v-else class="empty">
            <span class="empty-ico" v-html="icon('reports')"></span>
            <div>{{ t('reports.noData') }}</div>
          </div>
        </div>

        <div class="card">
          <h3>{{ t('reports.spendTrend') }}</h3>
          <div v-if="insights.breakdown?.length" class="bars">
            <div v-for="(b, i) in insights.breakdown" :key="b.category" class="bar-row">
              <div class="bar-top">
                <span class="bar-label" :title="b.category"><span class="sw" :style="{ background: color(i) }"></span>{{ b.category }}</span>
                <span class="bar-val num">{{ cur }} {{ b.monthly.toFixed(2) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barW(b) + '%', background: color(i) }"></div>
              </div>
            </div>
          </div>
          <div v-else class="empty">
            <span class="empty-ico" v-html="icon('reports')"></span>
            <div>{{ t('reports.empty') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 支出洞察 -->
    <div v-else-if="active === 'insights'">
      <div class="card">
        <h3 class="sh"><span class="ico" v-html="icon('trending')"></span>{{ t('reports.ranking') }}</h3>
        <div class="ledger">
          <div v-for="(s, i) in ranking" :key="s.id" class="lr">
            <div class="lr-row">
              <span class="lr-rank num">{{ i + 1 }}</span>
              <SubIcon :icon="s.icon" :name="s.name" :size="32" />
              <div class="lr-main">
                <div class="lr-name">{{ s.name }}<span v-if="s.plan" class="lr-plan"> · {{ s.plan }}</span></div>
                <div class="lr-sub">{{ catName(s.category_id) }}</div>
                <div v-if="s.remark" class="lr-remark">{{ s.remark }}</div>
              </div>
              <div class="lr-amt num">
                {{ cur }} {{ (s.amount_in_base || 0).toFixed(2) }}
                <small>{{ t('reports.monthly') }}</small>
              </div>
            </div>
            <div class="lr-bar"><i :style="{ width: rankW(s) + '%' }"></i></div>
          </div>
          <div v-if="!ranking.length" class="empty sm">{{ t('reports.empty') }}</div>
        </div>
      </div>

      <div class="grid two">
        <div class="card">
          <h3 class="sh"><span class="ico" v-html="icon('clock')"></span>{{ t('reports.upcoming') }}</h3>
          <div class="ledger">
            <div v-for="s in upcoming" :key="s.id" class="lr-row">
              <SubIcon :icon="s.icon" :name="s.name" :size="32" />
              <div class="lr-main">
                <div class="lr-name">{{ s.name }}</div>
                <div class="lr-sub">{{ s.plan ? s.plan + ' · ' : '' }}{{ catName(s.category_id) }}</div>
                <div v-if="s.remark" class="lr-remark">{{ s.remark }}</div>
              </div>
              <div class="lr-side">
                <div class="lr-amt num">{{ s.amount.toFixed(2) }} {{ s.currency }}</div>
                <span class="tag num" :class="statusOf(s)">{{ s.next_renewal_date }}</span>
              </div>
            </div>
            <div v-if="!upcoming.length" class="empty sm">{{ t('reports.empty') }}</div>
          </div>
        </div>
        <div class="card">
          <h3 class="sh"><span class="ico" v-html="icon('alert')"></span>{{ t('reports.expired') }}</h3>
          <div class="ledger">
            <div v-for="s in expired" :key="s.id" class="lr-row">
              <SubIcon :icon="s.icon" :name="s.name" :size="32" />
              <div class="lr-main">
                <div class="lr-name">{{ s.name }}</div>
                <div class="lr-sub">{{ s.plan ? s.plan + ' · ' : '' }}{{ catName(s.category_id) }}</div>
                <div v-if="s.remark" class="lr-remark">{{ s.remark }}</div>
              </div>
              <div class="lr-side">
                <div class="lr-amt num">{{ s.amount.toFixed(2) }} {{ s.currency }}</div>
                <span class="tag late num">{{ s.next_renewal_date }}</span>
              </div>
            </div>
            <div v-if="!expired.length" class="empty sm">{{ t('reports.empty') }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 class="sh"><span class="ico" v-html="icon('package')"></span>{{ t('reports.oneTime') }}</h3>
        <div class="ledger">
          <div v-for="s in oneTime" :key="s.id" class="lr-row">
            <SubIcon :icon="s.icon" :name="s.name" :size="32" />
            <div class="lr-main">
              <div class="lr-name">{{ s.name }}<span v-if="s.plan" class="lr-plan"> · {{ s.plan }}</span></div>
              <div class="lr-sub">{{ catName(s.category_id) }}</div>
              <div v-if="s.remark" class="lr-remark">{{ s.remark }}</div>
            </div>
            <div class="lr-side">
              <div class="lr-amt num">{{ s.amount.toFixed(2) }} {{ s.currency }}</div>
              <div class="lr-date num" :title="t('sub.startDate')">{{ s.start_date }}</div>
            </div>
          </div>
          <div v-if="!oneTime.length" class="empty sm">{{ t('reports.empty') }}</div>
        </div>
      </div>
    </div>

    <!-- 分类明细 -->
    <div v-else-if="active === 'categoryDetail'">
      <div class="grid two">
        <div class="card">
          <h3 class="sh split">
            <span class="sh"><span class="ico" v-html="icon('renew')"></span>{{ t('reports.recurringSubs') }}</span>
            <span class="total num">{{ cur }} {{ (detail.recurring_monthly_total || 0).toFixed(2) }} / {{ t('reports.monthly') }}</span>
          </h3>
          <div class="table-wrap">
            <table>
              <thead><tr><th>{{ t('reports.category') }}</th><th class="r">{{ t('reports.count') }}</th><th class="r">{{ t('reports.monthly') }}</th></tr></thead>
              <tbody>
                <tr v-for="r in detail.recurring" :key="r.category">
                  <td>{{ r.category }}</td><td class="r">{{ r.count }}</td><td class="r">{{ cur }} {{ r.monthly.toFixed(2) }}</td>
                </tr>
                <tr v-if="!detail.recurring?.length"><td colspan="3" class="muted">{{ t('reports.empty') }}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="card">
          <h3 class="sh split">
            <span class="sh"><span class="ico" v-html="icon('package')"></span>{{ t('reports.permanentBuy') }}</span>
            <span class="total num">{{ cur }} {{ (detail.one_time_total || 0).toFixed(2) }}</span>
          </h3>
          <div class="table-wrap">
            <table>
              <thead><tr><th>{{ t('reports.category') }}</th><th class="r">{{ t('reports.count') }}</th><th class="r">{{ t('reports.amount') }}</th></tr></thead>
              <tbody>
                <tr v-for="r in detail.one_time" :key="r.category">
                  <td>{{ r.category }}</td><td class="r">{{ r.count }}</td><td class="r">{{ cur }} {{ r.total.toFixed(2) }}</td>
                </tr>
                <tr v-if="!detail.one_time?.length"><td colspan="3" class="muted">{{ t('reports.empty') }}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 近期付款 -->
    <div v-else class="card">
      <h3 class="sh"><span class="ico" v-html="icon('wallet')"></span>{{ t('reports.recentPayments') }}</h3>
      <div class="ledger">
        <div v-for="p in payments" :key="p.id + '-' + p.date" class="lr-row">
          <SubIcon :icon="p.icon" :name="p.name" :size="32" />
          <div class="lr-main">
            <div class="lr-name">{{ p.name }}<span v-if="p.plan" class="lr-plan"> · {{ p.plan }}</span></div>
            <div class="lr-sub">{{ p.category || catName(null) }} · {{ p.billing_type === 'recurring' ? t('sub.recurring') : t('sub.oneTime') }}</div>
            <div v-if="p.remark" class="lr-remark">{{ p.remark }}</div>
          </div>
          <div class="lr-side">
            <div class="lr-amt num">{{ p.amount.toFixed(2) }} {{ p.currency }}</div>
            <div class="lr-date num">{{ p.date }}</div>
          </div>
        </div>
        <div v-if="!payments.length" class="empty sm">{{ t('reports.empty') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'
import { statusOf } from '../lifeline'
import SubIcon from '../components/SubIcon.vue'

const { t } = useI18n()
const androidPreview = inject('preview', null)
const auth = useAuth()
const tabs = ['overview', 'insights', 'categoryDetail', 'recentPayments']
const active = ref('overview')
const cur = auth.user?.base_currency || 'CNY'

const insights = ref({ breakdown: [] })
const detail = ref({ recurring: [], one_time: [] })
const ranking = ref([])
const oneTime = ref([])
const upcoming = ref([])
const expired = ref([])
const payments = ref([])
const cats = ref([])

function catName(id) {
  if (id == null) return t('sub.uncategorized')
  const c = cats.value.find((x) => x.id === id)
  return c ? c.name : t('sub.uncategorized')
}

// 分类配色：刻意避开状态色（绿/琥珀/红），状态色只表示到期状态
const PALETTE = ['#3b6fd8', '#7a5af8', '#0e9aa7', '#c0408f', '#5b6b7f', '#3aa0e0', '#8a6d3b', '#9b7be0']
function color(i) { return PALETTE[i % PALETTE.length] }

const segments = computed(() => (insights.value.breakdown || []).filter((b) => b.percent > 0))
const donutStyle = computed(() => {
  const bd = insights.value.breakdown || []
  if (!bd.length) return { background: 'var(--border)' }
  let acc = 0
  const stops = []
  bd.forEach((b, i) => {
    const start = acc
    acc += b.percent
    stops.push(`${color(i)} ${start}% ${acc}%`)
  })
  if (acc < 100) stops.push(`var(--surface-2) ${acc}% 100%`)
  return { background: `conic-gradient(${stops.join(',')})` }
})
const maxMonthly = computed(() => Math.max(1, ...(insights.value.breakdown || []).map((b) => b.monthly)))
function barW(b) { return Math.round((b.monthly / maxMonthly.value) * 100) }
const maxRank = computed(() => Math.max(0.01, ...ranking.value.map((s) => s.amount_in_base || 0)))
function rankW(s) { return Math.max(1, Math.round(((s.amount_in_base || 0) / maxRank.value) * 100)) }
const recurringCount = computed(() => (detail.value.recurring || []).reduce((a, r) => a + r.count, 0))

async function loadOverview() {
  const [ins, det] = await Promise.all([
    api.get('/api/reports/insights'),
    api.get('/api/reports/category-detail')
  ])
  insights.value = ins.data
  detail.value = det.data
}
async function loadInsights() {
  const [r, o, u, e] = await Promise.all([
    api.get('/api/reports/ranking'),
    api.get('/api/reports/one-time'),
    api.get('/api/reports/upcoming'),
    api.get('/api/reports/expired')
  ])
  ranking.value = r.data; oneTime.value = o.data; upcoming.value = u.data; expired.value = e.data
}
async function loadDetail() { detail.value = (await api.get('/api/reports/category-detail')).data }
async function loadPayments() { payments.value = (await api.get('/api/reports/recent-payments')).data.items }

function loadActive() {
  if (active.value === 'overview') loadOverview()
  else if (active.value === 'insights') loadInsights()
  else if (active.value === 'categoryDetail') loadDetail()
  else loadPayments()
}

async function exportCsv() {
  try {
    const { data } = await api.get('/api/reports/export.csv', { responseType: 'text' })
    const blob = new Blob([data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'easysub-report.csv'
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  } catch { /* ignore */ }
}

watch(active, loadActive)
onMounted(async () => {
  cats.value = (await api.get('/api/categories').catch(() => ({ data: [] }))).data || []
  loadActive()
})
</script>

<style scoped>
.ico { display: inline-flex; width: 17px; height: 17px; flex-shrink: 0; }
.ico :deep(svg) { width: 100%; height: 100%; }
.num { font-variant-numeric: tabular-nums; }
.r { text-align: right; }

.tabs-scroll { overflow-x: auto; margin-bottom: 16px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.tabs-scroll::-webkit-scrollbar { display: none; }
.seg button { white-space: nowrap; }

.two { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 16px; }
.two + .card { margin-top: 16px; }
.sh { display: flex; align-items: center; gap: 8px; }
.sh .ico { color: var(--text-soft); }
.sh.split { justify-content: space-between; flex-wrap: wrap; gap: 6px 12px; }
.total { font-size: 13px; font-weight: 550; color: var(--text-soft); }

/* ---------- 指标条 ---------- */
.stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 0; }
.stat { padding: 18px 20px; border-left: 1px solid var(--border); min-width: 0; }
.stat:first-child { border-left: none; }
.stat-l { font-size: 13px; color: var(--text-soft); }
.stat-v { font-size: 24px; font-weight: 650; letter-spacing: -.02em; margin-top: 4px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.stat-v small { font-size: 13px; font-weight: 550; color: var(--text-soft); letter-spacing: 0; }

/* ---------- 环形图 ---------- */
.donut-wrap { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.donut { width: 156px; height: 156px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.donut-hole { width: 104px; height: 104px; border-radius: 50%; background: var(--surface);
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.dh-v { font-size: 20px; font-weight: 650; letter-spacing: -.02em; }
.dh-l { font-size: 11.5px; color: var(--text-soft); }
.legend { flex: 1; min-width: 150px; display: flex; flex-direction: column; gap: 7px; }
.lg { display: flex; align-items: center; gap: 9px; font-size: 13.5px; }
.sw { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; display: inline-block; }
.lg-n { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lg-p { color: var(--text-soft); }

/* ---------- 横向条形 ---------- */
.bars { display: flex; flex-direction: column; gap: 12px; }
.bar-top { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; margin-bottom: 5px; }
.bar-label { display: inline-flex; align-items: center; gap: 8px; font-size: 13.5px; min-width: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-val { font-size: 13px; color: var(--text-soft); flex-shrink: 0; }
.bar-track { background: var(--surface-2); border-radius: 999px; height: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; transition: width .5s var(--ease-out); }

/* ---------- 账本式列表 ---------- */
.ledger { display: flex; flex-direction: column; }
.lr { border-bottom: 1px solid var(--border); padding-bottom: 10px; }
.lr:last-child, .ledger > .lr-row:last-child { border-bottom: none; }
.lr .lr-row { border-bottom: none; padding-bottom: 6px; }
.lr-row { display: flex; align-items: center; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--border); min-width: 0; }
.lr-rank { width: 20px; flex-shrink: 0; text-align: right; font-size: 13px; font-weight: 600; color: var(--text-soft); }
.lr-main { flex: 1; min-width: 0; line-height: 1.3; }
.lr-name { font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lr-plan { font-weight: 500; color: var(--text-soft); }
.lr-sub, .lr-remark { font-size: 12.5px; color: var(--text-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lr-remark { font-style: italic; }
.lr-side { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.lr-amt { font-size: 14px; font-weight: 600; text-align: right; white-space: nowrap; flex-shrink: 0; }
.lr-amt small { display: block; font-size: 11.5px; font-weight: 500; color: var(--text-soft); }
.lr-date { font-size: 12.5px; color: var(--text-soft); }
.lr-bar { height: 4px; border-radius: 999px; margin-left: 32px; }
.lr-bar i { display: block; height: 100%; border-radius: inherit;
  background: color-mix(in srgb, var(--primary) 35%, transparent); transition: width .5s var(--ease-out); }

.empty { padding: 28px 12px; }
.empty.sm { padding: 18px 12px; font-size: 14px; }
.empty-ico { display: inline-flex; width: 32px; height: 32px; color: var(--text-faint); margin-bottom: 6px; }
.empty-ico :deep(svg) { width: 100%; height: 100%; margin: 0; }

@media (max-width: 860px) {
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stat:nth-child(3) { border-left: none; }
  .stat:nth-child(n + 3) { border-top: 1px solid var(--border); }
  .two { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 720px) {
  .page-head .btn { min-height: 40px; }
  .seg button { min-height: 36px; }
  .stat { padding: 14px 16px; }
  .stat-v { font-size: 20px; }
  .donut-wrap { justify-content: center; }
  .legend { flex-basis: 100%; }
  .lr-row { gap: 10px; }
  .lr-bar { margin-left: 30px; }
}
</style>
