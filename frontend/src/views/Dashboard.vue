<template>
  <div>
    <div v-if="loading" class="muted">{{ t('common.loading') }}</div>
    <template v-else>
      <!-- 欢迎 hero -->
      <div class="hero card">
        <div>
          <div class="hi">{{ t('dashboard.greeting', { name: auth.user?.username || '' }) }}</div>
          <div class="sub muted">{{ t('dashboard.subtitle') }}</div>
        </div>
        <router-link to="/subscriptions" class="btn">+ {{ t('sub.add') }}</router-link>
      </div>

      <!-- KPI -->
      <div class="grid stats">
        <div class="card stat s1">
          <div class="badge" v-html="icon('wallet')"></div>
          <div><div class="muted">{{ t('dashboard.monthSpend') }}</div><div class="big">{{ fmt(data.month_spend) }}</div></div>
        </div>
        <div class="card stat s2">
          <div class="badge" v-html="icon('trending')"></div>
          <div><div class="muted">{{ t('dashboard.yearSpend') }}</div><div class="big">{{ fmt(data.year_spend) }}</div></div>
        </div>
        <div class="card stat s3">
          <div class="badge" v-html="icon('package')"></div>
          <div><div class="muted">{{ t('dashboard.active') }}</div><div class="big">{{ data.active_count }}</div></div>
        </div>
        <div class="card stat s4" :class="{ alert: expiredCount > 0 }">
          <div class="badge" v-html="icon('alert')"></div>
          <div><div class="muted">{{ t('dashboard.overdue') }}</div><div class="big">{{ expiredCount }}</div></div>
        </div>
      </div>

      <!-- 月度预算 -->
      <div class="card budget" v-if="data.monthly_budget">
        <div class="bc-h">
          <span class="muted">{{ t('remind.budget') }}</span>
          <b :class="{ over: overBudget }">{{ fmt(data.month_spend) }} / {{ fmt(data.monthly_budget) }}</b>
        </div>
        <div class="bc-bar"><div class="bc-fill" :class="{ over: overBudget }" :style="{ width: budgetPct + '%' }"></div></div>
        <div class="muted bc-note">
          {{ overBudget ? t('remind.over') : t('remind.budgetLeft') }}：{{ fmt(Math.abs(data.monthly_budget - data.month_spend)) }}
        </div>
      </div>

      <div class="grid main">
        <!-- 即将到期 -->
        <div class="card">
          <div class="card-h">
            <h3>{{ t('dashboard.upcoming') }}</h3>
            <router-link to="/calendar" class="more">{{ t('dashboard.viewAll') }} →</router-link>
          </div>
          <p v-if="!data.upcoming.length" class="muted">{{ t('dashboard.none') }}</p>
          <div v-for="s in data.upcoming" :key="s.id" class="line">
            <span class="l-name">
              <img v-if="isImg(s.icon)" :src="s.icon" class="mini-ico" />
              <span v-else class="mini-emoji">{{ emojiOf(s) }}</span>
              <span class="l-txt">{{ s.name }}</span>
            </span>
            <span class="l-right">
              <span class="tag" :class="dueClass(s)">{{ dueText(s) }}</span>
              <b>{{ fmt(s.amount_in_base) }}</b>
            </span>
          </div>
        </div>

        <!-- 分类占比 -->
        <div class="card">
          <div class="card-h"><h3>{{ t('dashboard.byCategory') }}</h3>
            <router-link to="/reports" class="more">{{ t('dashboard.viewAll') }} →</router-link></div>
          <div v-if="breakdown.length" class="donut-wrap">
            <div class="donut" :style="donutStyle"><div class="donut-hole"></div></div>
            <div class="legend">
              <div v-for="(b, i) in breakdown.slice(0, 6)" :key="b.category" class="lg">
                <span class="dot" :style="{ background: color(i) }"></span>
                <span class="lg-n">{{ b.category }}</span>
                <span class="muted">{{ b.percent }}%</span>
              </div>
            </div>
          </div>
          <p v-else class="muted">{{ t('dashboard.none') }}</p>
        </div>
      </div>

      <!-- 分类总览：按分类展示全部订阅 + 颜色警示 -->
      <div class="card" v-if="catGroups.length">
        <h3>{{ t('dashboard.catOverview') }}</h3>
        <div class="cat-cols">
          <div v-for="g in catGroups" :key="g.key" class="cat-col">
            <div class="cc-head">
              <span>{{ g.icon }} {{ g.name }}</span>
              <span class="cc-count">{{ g.items.length }}</span>
            </div>
            <div v-for="s in g.items" :key="s.id" class="cc-item" :class="statusOf(s)">
              <span class="cc-dot"></span>
              <img v-if="isImg(s.icon)" :src="s.icon" class="mini-ico" />
              <span v-else class="mini-emoji sm">{{ emojiOf(s) }}</span>
              <span class="cc-n">{{ s.name }}</span>
              <span class="cc-d">{{ s.next_renewal_date ? dueText(s) : t('sub.oneTime') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近订阅 -->
      <div class="card">
        <h3>{{ t('dashboard.recent') }}</h3>
        <p v-if="!data.recent.length" class="muted">{{ t('dashboard.none') }}</p>
        <div class="recent-grid">
          <div v-for="s in data.recent" :key="s.id" class="rc">
            <img v-if="isImg(s.icon)" :src="s.icon" class="rc-ico-img" />
            <span v-else class="rc-ico">{{ emojiOf(s) }}</span>
            <div class="rc-main"><div class="rc-n">{{ s.name }}</div>
              <div class="muted rc-a">{{ fmt(s.amount_in_base) }}</div></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'

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

const PALETTE = ['#5b5bd6', '#06b6d4', '#16a34a', '#f59e0b', '#ef4444', '#a855f7', '#0ea5e9', '#ec4899']
function color(i) { return PALETTE[i % PALETTE.length] }

function fmt(v) {
  const cur = auth.user?.base_currency || 'CNY'
  return `${cur} ${Number(v || 0).toFixed(2)}`
}
function isImg(v) { return typeof v === 'string' && (v.startsWith('/') || v.startsWith('http')) }
function emojiOf(s) { return s.icon && !isImg(s.icon) ? s.icon : '🔖' }
function daysLeft(s) {
  if (!s.next_renewal_date) return null
  return Math.ceil((new Date(s.next_renewal_date) - new Date()) / 86400000)
}
function dueText(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  return d <= 0 ? t('dashboard.today') : t('dashboard.daysLeft', { n: d })
}
function dueClass(s) {
  const d = daysLeft(s)
  return d !== null && d <= 3 ? 'warn' : ''
}
function statusOf(s) {
  if (s.billing_type !== 'recurring' || !s.next_renewal_date) return 'ok'
  const d = daysLeft(s)
  if (d < 0) return 'overdue'
  if (d <= 7) return 'soon'
  return 'ok'
}

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
      icon: key === 'none' ? '🗂️' : (c?.icon || '📁'),
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
  if (acc < 100) stops.push(`var(--border) ${acc}% 100%`)
  return { background: `conic-gradient(${stops.join(',')})` }
})

onMounted(async () => {
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
})
</script>

<style scoped>
.hero { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px;
  background: linear-gradient(120deg, var(--primary-soft), var(--surface)); }
.hi { font-size: 20px; font-weight: 700; }
.sub { font-size: 14px; margin-top: 2px; }

.stats { grid-template-columns: repeat(4, 1fr); margin-bottom: 16px; }
.stat { display: flex; align-items: center; gap: 14px; }
.stat .badge { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0; }
.stat .badge :deep(svg) { width: 24px; height: 24px; }
.stat.s1 .badge { background: #eef0ff; color: #5b5bd6; }
.stat.s2 .badge { background: #e0f7f1; color: #0e9f6e; }
.stat.s3 .badge { background: #fff1e6; color: #f59e0b; }
.stat.s4 .badge { background: #fee2e2; color: #ef4444; }
.stat.s4.alert { border-color: var(--danger); }
.stat .big { font-size: 24px; font-weight: 700; margin-top: 2px; letter-spacing: -.02em; }

.budget { margin-bottom: 16px; }
.bc-h { display: flex; justify-content: space-between; align-items: center; font-size: 14px; margin-bottom: 8px; }
.bc-h b.over { color: var(--danger); }
.bc-bar { height: 10px; border-radius: 6px; background: var(--surface-2); overflow: hidden; }
.bc-fill { height: 100%; background: var(--primary); border-radius: 6px; transition: width .4s ease; }
.bc-fill.over { background: var(--danger); }
.bc-note { font-size: 12px; margin-top: 6px; }
.main { grid-template-columns: 1.2fr 1fr; margin-bottom: 16px; }
.card-h { display: flex; justify-content: space-between; align-items: center; }
.card-h h3 { margin: 0; }
.more { font-size: 13px; }
h3 { margin-top: 0; }
.line { display: flex; justify-content: space-between; align-items: center; padding: 9px 0;
  border-bottom: 1px solid var(--border); font-size: 14px; }
.line:last-child { border-bottom: none; }
.l-name { display: flex; align-items: center; gap: 8px; min-width: 0; }
.l-txt { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.l-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
/* 列表/分类项中的小图标：图片或 emoji 统一尺寸 */
.mini-ico { width: 20px; height: 20px; border-radius: 5px; object-fit: contain; flex-shrink: 0;
  border: 1px solid var(--border); background: var(--surface-2); }
.mini-emoji { width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0; }
.mini-emoji.sm { font-size: 14px; }
.tag.warn { background: #fef3c7; color: #b45309; }

.donut-wrap { display: flex; align-items: center; gap: 18px; margin-top: 8px; }
.donut { width: 120px; height: 120px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; }
.donut-hole { width: 74px; height: 74px; border-radius: 50%; background: var(--surface); }
.legend { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.lg { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.lg-n { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* 分类总览 */
.cat-cols { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 6px; }
.cat-col { border: 1px solid var(--border); border-radius: 12px; padding: 12px; }
.cc-head { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 14px; margin-bottom: 8px; }
.cc-count { background: var(--surface-2); color: var(--text-soft); border-radius: 20px; padding: 1px 8px; font-size: 12px; }
.cc-item { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 5px 0; }
.cc-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); flex-shrink: 0; }
.cc-item.soon .cc-dot { background: var(--warning); }
.cc-item.overdue .cc-dot { background: var(--danger); }
.cc-n { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cc-d { font-size: 12px; color: var(--text-soft); white-space: nowrap; }
.cc-item.overdue .cc-d { color: var(--danger); font-weight: 600; }
.cc-item.soon .cc-d { color: var(--warning); font-weight: 600; }

.recent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.rc { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid var(--border); border-radius: 10px; }
.rc-ico { font-size: 20px; width: 26px; text-align: center; flex-shrink: 0; }
.rc-ico-img { width: 26px; height: 26px; border-radius: 7px; object-fit: contain; flex-shrink: 0;
  border: 1px solid var(--border); background: var(--surface-2); }
.rc-main { min-width: 0; }
.rc-n { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rc-a { font-size: 12px; }

@media (max-width: 980px) { .stats { grid-template-columns: 1fr 1fr; } .main { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .stats { grid-template-columns: 1fr 1fr; } }
</style>
