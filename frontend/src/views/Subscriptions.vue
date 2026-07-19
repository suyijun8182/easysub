<template>
  <div>
    <div class="head">
      <h1>{{ t('nav.subscriptions') }}</h1>
      <button class="btn" @click="openNew">+ {{ t('sub.add') }}</button>
    </div>

    <div class="bar">
      <div class="seg">
        <button :class="{ on: filter === '' }" @click="setFilter('')">{{ t('sub.filterAll') }}</button>
        <button :class="{ on: filter === 'recurring' }" @click="setFilter('recurring')">{{ t('sub.filterRecurring') }}</button>
        <button :class="{ on: filter === 'one_time' }" @click="setFilter('one_time')">{{ t('sub.filterOneTime') }}</button>
      </div>
      <span class="muted drag-hint">⠿ {{ t('sub.dragHint') }}</span>
    </div>

    <div v-if="!subs.length" class="card muted">{{ t('dashboard.none') }}</div>

    <!-- 按分类分组 -->
    <div v-for="g in grouped" :key="g.key" class="cat-group"
         :class="{ 'drop-cat': dragOverCat === g.key }"
         draggable="true"
         @dragstart="onCatDragStart(g.key, $event)"
         @dragover.prevent="onCatDragOver(g.key)"
         @dragend="clearDrag"
         @drop="onCatDrop(g.key)">
      <div class="cat-head">
        <span class="grip">⠿</span>
        <span class="cat-ico">{{ g.icon }}</span>
        <span class="cat-name">{{ g.name }}</span>
        <span class="cat-count">{{ g.items.length }}</span>
      </div>

      <div class="sub-grid">
        <div v-for="s in g.items" :key="s.id" class="card sub-card"
             :class="{ inactive: !s.is_active, expired: isExpired(s), soon: isSoon(s), 'drop-card': dragOverSub === s.id }"
             draggable="true"
             @dragstart.stop="onCardDragStart(g.key, s.id, $event)"
             @dragover.prevent.stop="onCardDragOver(g.key, s.id)"
             @dragend="clearDrag"
             @drop.stop="onCardDrop(g.key, s.id)">
          <div class="sc-head">
            <img v-if="isImg(s.icon)" :src="s.icon" class="sc-ico" />
            <span v-else class="sc-ico emoji">{{ s.icon || '🔖' }}</span>
            <div class="sc-title">
              <div class="sc-name">{{ s.name }}</div>
              <div class="muted sc-plan" v-if="s.plan">{{ s.plan }}</div>
            </div>
            <span class="tag" :class="s.billing_type">
              {{ s.billing_type === 'recurring' ? t('sub.recurring') : t('sub.oneTime') }}
            </span>
          </div>

          <div class="sc-amount">
            {{ s.amount.toFixed(2) }} <span class="muted cur">{{ s.currency }}</span>
            <span v-if="s.billing_type === 'recurring'" class="muted cycle">/ {{ cycleText(s) }}</span>
          </div>

          <div v-if="isExpired(s)" class="expired-banner">⚠️ {{ t('sub.expiredTag') }}</div>
          <div v-else-if="isSoon(s)" class="soon-banner">⏰ {{ t('sub.soonTag') }}</div>

          <div v-if="s.remark" class="sc-remark">📝 {{ s.remark }}</div>

          <div class="sc-rows">
            <div v-if="s.next_renewal_date" class="sc-row">
              <span class="muted">📅 {{ t('sub.nextRenewal') }}</span>
              <span class="due" :class="dueClass(s)">{{ s.next_renewal_date }} · {{ dueText(s) }}</span>
            </div>
            <div class="sc-row" v-if="s.ipv4">
              <span class="muted">🌐 IPv4</span><span class="mono">{{ s.ipv4 }}</span>
            </div>
            <div class="sc-row" v-if="s.ipv6">
              <span class="muted">🌐 IPv6</span><span class="mono">{{ s.ipv6 }}</span>
            </div>
            <div class="sc-row" v-if="payName(s)">
              <span class="muted">💳 {{ t('sub.payment') }}</span><span>{{ payName(s) }}</span>
            </div>
            <div class="sc-row" v-if="s.billing_type === 'recurring'">
              <span class="muted">🔁 {{ t('sub.autoRenew') }}</span>
              <span>{{ s.auto_renew ? '✓' : '✗' }}</span>
            </div>
            <div class="sc-row" v-if="s.family_members && s.family_members.length">
              <span class="muted">👨‍👩‍👧 {{ t('sub.family') }}</span>
              <span>{{ s.family_members.join('、') }}</span>
            </div>
          </div>

          <div class="sc-acts">
            <button class="btn sm ghost" @click="openEdit(s)">{{ t('sub.edit') }}</button>
            <button v-if="s.billing_type === 'recurring'" class="btn sm" @click="askRenew(s)">♻️ {{ t('sub.renew') }}</button>
            <button class="btn sm danger" @click="askDelete(s)">{{ t('sub.delete') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 续费确认弹窗 -->
    <div v-if="renewTarget" class="modal-mask" @click.self="renewTarget = null">
      <div class="modal" style="width:460px">
        <h3>♻️ {{ t('sub.renewTitle') }}</h3>
        <p style="font-size:14px;line-height:1.6">{{ t('sub.renewMsg', { name: renewTarget.name }) }}</p>
        <label class="opt" :class="{ on: renewMode === 'today' }">
          <input type="radio" value="today" v-model="renewMode" />
          <div>
            <div>{{ t('sub.renewToday') }}</div>
            <div class="muted opt-d">→ {{ previewToday }}</div>
          </div>
        </label>
        <label class="opt" :class="{ on: renewMode === 'due' }">
          <input type="radio" value="due" v-model="renewMode" />
          <div>
            <div>{{ t('sub.renewDue') }}</div>
            <div class="muted opt-d">→ {{ previewDue }}</div>
          </div>
        </label>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="renewTarget = null">{{ t('sub.cancel') }}</button>
          <button class="btn" :disabled="renewing" @click="confirmRenew">{{ t('sub.confirm') }}</button>
        </div>
      </div>
    </div>

    <!-- 删除确认（需验证密码） -->
    <div v-if="delTarget" class="modal-mask" @click.self="delTarget = null">
      <div class="modal" style="width:420px">
        <h3>🗑️ {{ t('sub.deleteTitle') }}</h3>
        <p style="font-size:14px;line-height:1.6">{{ t('sub.deletePwdTip', { name: delTarget.name }) }}</p>
        <input v-model="delPwd" type="password" :placeholder="t('sub.pwdPh')" @keyup.enter="confirmDelete" />
        <p v-if="delErr" class="err">{{ delErr }}</p>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="delTarget = null">{{ t('sub.cancel') }}</button>
          <button class="btn danger" :disabled="deleting || !delPwd" @click="confirmDelete">{{ t('sub.delete') }}</button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑订阅 -->
    <div v-if="showForm" class="modal-mask" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ form.id ? t('sub.edit') : t('sub.add') }}</h3>

        <div class="block">
          <div class="block-t">{{ t('sub.secService') }}</div>
          <div class="row">
            <div class="icon-pick">
              <img v-if="isImg(form.icon)" :src="form.icon" class="ico-lg" />
              <span v-else class="ico-lg emoji">{{ form.icon || '🔖' }}</span>
            </div>
            <div style="flex:2;position:relative">
              <label>{{ t('sub.name') }}</label>
              <input v-model="form.name" @input="onNameInput" autocomplete="off" />
              <div v-if="suggestions.length" class="suggest">
                <div v-for="s in suggestions" :key="s.slug" class="suggest-i" @click="pickService(s)">
                  <img :src="s.icon" class="ico" /> {{ s.name }}
                </div>
              </div>
            </div>
            <div style="flex:1">
              <label>{{ t('sub.plan') }}</label>
              <input v-model="form.plan" :placeholder="t('sub.planPh')" />
            </div>
          </div>
          <label>{{ t('sub.remark') }}</label>
          <input v-model="form.remark" :placeholder="t('sub.remarkPh')" />

          <!-- VPS：IP 地址（选填） -->
          <template v-if="isVpsCategory">
            <label>{{ t('sub.ipLabel') }}</label>
            <div class="row">
              <div style="flex:1">
                <input v-model="form.ipv4" :placeholder="t('sub.ipv4')" />
              </div>
              <div style="flex:1">
                <input v-model="form.ipv6" :placeholder="t('sub.ipv6')" />
              </div>
            </div>
          </template>

          <button class="btn ghost sm" style="margin-top:8px" @click="openBrowser">📚 {{ t('sub.browse') }}</button>

          <details class="icon-lib">
            <summary>{{ t('sub.icon') }} — {{ t('sub.iconLibrary') }} / URL / {{ t('sub.uploadIcon') }}</summary>
            <input v-model="form.icon" placeholder="🔖 emoji / /static/... / https://..." style="margin:8px 0" />
            <div class="row" style="margin-bottom:8px">
              <input v-model="iconUrl" :placeholder="t('sub.iconUrl')" style="flex:1" />
              <button class="btn ghost sm" @click="importIconUrl">{{ t('sub.iconUrlImport') }}</button>
              <label class="btn ghost sm" style="width:auto">{{ t('sub.uploadIcon') }}
                <input type="file" accept="image/*" hidden @change="uploadIcon" />
              </label>
            </div>
            <div class="lib-grid">
              <img v-for="it in iconLib" :key="it.slug" :src="it.icon" :title="it.name"
                   class="lib-ico" @click="form.icon = it.icon" />
            </div>
          </details>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secPrice') }}</div>
          <div class="row">
            <div style="flex:1">
              <label>{{ t('sub.amount') }}</label>
              <input v-model.number="form.amount" type="number" step="0.01" />
            </div>
            <div style="flex:1">
              <label>{{ t('sub.currency') }}</label>
              <select v-model="form.currency">
                <option v-for="c in currencies" :key="c.code" :value="c.code">{{ c.code }} {{ c.symbol }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secBilling') }}</div>
          <div class="row">
            <div style="flex:1">
              <label>{{ t('sub.billingType') }}</label>
              <select v-model="form.billing_type">
                <option value="recurring">{{ t('sub.recurring') }}</option>
                <option value="one_time">{{ t('sub.oneTime') }}</option>
              </select>
            </div>
            <template v-if="form.billing_type === 'recurring'">
              <div style="flex:1">
                <label>{{ t('sub.cycleCount') }}</label>
                <input v-model.number="form.cycle_count" type="number" min="1" />
              </div>
              <div style="flex:1">
                <label>{{ t('sub.cycle') }}</label>
                <select v-model="form.cycle">
                  <option value="day">{{ t('sub.day') }}</option>
                  <option value="week">{{ t('sub.week') }}</option>
                  <option value="month">{{ t('sub.month') }}</option>
                  <option value="year">{{ t('sub.year') }}</option>
                </select>
              </div>
            </template>
          </div>
          <div class="row">
            <div style="flex:1">
              <label>{{ t('sub.startDate') }}</label>
              <input v-model="form.start_date" type="date" />
            </div>
            <div style="flex:1" v-if="form.billing_type === 'recurring'">
              <label>{{ t('sub.nextRenewal') }} <span class="auto-tip">· 自动</span></label>
              <input v-model="form.next_renewal_date" type="date" />
            </div>
          </div>
          <div class="row" v-if="form.billing_type === 'recurring'">
            <div style="flex:1">
              <label>{{ t('sub.remindDays') }}</label>
              <input v-model="form.remind_days_before" placeholder="7,6,5,4,3,2,1" />
            </div>
            <div style="flex:1">
              <label>{{ t('sub.active') }}</label>
              <select v-model="form.is_active"><option :value="true">✓</option><option :value="false">✗</option></select>
            </div>
            <div style="flex:1">
              <label>{{ t('sub.autoRenew') }}</label>
              <select v-model="form.auto_renew"><option :value="true">✓</option><option :value="false">✗</option></select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secClassify') }}</div>
          <div class="row">
            <div style="flex:1">
              <label>{{ t('sub.category') }}</label>
              <select v-model="form.category_id">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
              </select>
            </div>
            <div style="flex:1">
              <label>{{ t('sub.payment') }}</label>
              <select v-model="form.payment_method_id">
                <option :value="null">—</option>
                <option v-for="p in methods" :key="p.id" :value="p.id">{{ p.icon }} {{ p.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secFamily') }}</div>
          <div class="chips">
            <span v-for="(m, i) in form.family_members" :key="i" class="chip">
              {{ m }} <a href="#" @click.prevent="form.family_members.splice(i, 1)">✕</a>
            </span>
          </div>
          <div class="row">
            <input v-model="newMember" :placeholder="t('sub.familyPh')" @keyup.enter="addMember" style="flex:1" />
            <button class="btn ghost sm" @click="addMember">{{ t('sub.familyAdd') }}</button>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secBundle') }}</div>
          <div class="row radio-row">
            <label class="rb"><input type="radio" value="none" v-model="bundleMode" /> {{ t('sub.bundleNone') }}</label>
            <label class="rb"><input type="radio" value="join" v-model="bundleMode" /> {{ t('sub.bundleJoin') }}</label>
            <label class="rb"><input type="radio" value="create" v-model="bundleMode" /> {{ t('sub.bundleCreate') }}</label>
          </div>
          <select v-if="bundleMode === 'join'" v-model="form.bundle_id">
            <option :value="null">—</option>
            <option v-for="b in bundles" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
          <input v-if="bundleMode === 'create'" v-model="newBundleName" :placeholder="t('sub.bundleName')" />
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secExtra') }}</div>
          <label>{{ t('sub.website') }}</label>
          <input v-model="form.url" placeholder="https://..." />
          <label>{{ t('sub.notes') }}</label>
          <textarea v-model="form.notes" rows="2"></textarea>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secCalendar') }}</div>
          <label class="rb"><input type="checkbox" v-model="form.show_in_calendar" /> {{ t('sub.showInCalendar') }}</label>
        </div>

        <p v-if="formErr" class="err">{{ formErr }}</p>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="showForm = false">{{ t('sub.cancel') }}</button>
          <button class="btn" @click="save">{{ t('sub.save') }}</button>
        </div>
      </div>
    </div>

    <!-- 按分类浏览服务库 -->
    <div v-if="showBrowser" class="modal-mask browser" @click.self="showBrowser = false">
      <div class="modal">
        <div class="head" style="margin-bottom:10px">
          <h3 style="margin:0">📚 {{ t('sub.browseTitle') }}</h3>
          <button class="btn ghost sm" @click="showBrowser = false">{{ t('common.close') }}</button>
        </div>
        <p class="muted" style="font-size:13px;margin-top:0">{{ t('sub.pickHint') }}</p>
        <input v-model="browserQ" :placeholder="t('sub.searchPh')" style="margin-bottom:12px" />
        <div v-for="g in groupedLib" :key="g.key" class="lib-group">
          <div class="lib-group-t">{{ g.label }}</div>
          <div class="svc-grid">
            <button v-for="s in g.items" :key="s.slug" class="svc" @click="pickFromBrowser(s)">
              <img :src="s.icon" class="svc-ico" /> <span>{{ s.name }}</span>
            </button>
          </div>
        </div>
        <p v-if="!groupedLib.length" class="muted">{{ t('reports.empty') }}</p>
      </div>
    </div>

    <div class="toast-wrap">
      <div v-for="tst in toasts" :key="tst.id" class="toast" :class="tst.type">{{ tst.msg }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'

const { t } = useI18n()
const auth = useAuth()
const subs = ref([])
const currencies = ref([])
const categories = ref([])
const methods = ref([])
const bundles = ref([])
const iconLib = ref([])
const filter = ref('')
const showForm = ref(false)
const formErr = ref('')
const form = ref({})
const newMember = ref('')
const iconUrl = ref('')
const bundleMode = ref('none')
const newBundleName = ref('')
const suggestions = ref([])

const showBrowser = ref(false)
const browserQ = ref('')

const renewTarget = ref(null)
const renewMode = ref('today')
const renewing = ref(false)

const delTarget = ref(null)
const delPwd = ref('')
const delErr = ref('')
const deleting = ref(false)

const toasts = ref([])
let toastId = 0
function toast(msg, type = 'ok') {
  const id = ++toastId
  toasts.value.push({ id, msg, type })
  setTimeout(() => { toasts.value = toasts.value.filter((x) => x.id !== id) }, 2600)
}

function isImg(v) { return typeof v === 'string' && (v.startsWith('/') || v.startsWith('http')) }
function payName(s) {
  const p = methods.value.find((x) => x.id === s.payment_method_id)
  return p ? `${p.icon || ''} ${p.name}`.trim() : ''
}
function cycleText(s) {
  const n = s.cycle_count > 1 ? s.cycle_count + ' ' : ''
  return n + t('sub.' + s.cycle)
}
function daysLeft(s) {
  if (!s.next_renewal_date) return null
  return Math.ceil((new Date(s.next_renewal_date) - new Date()) / 86400000)
}
function dueText(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  if (d < 0) return t('sub.expiredTag')
  return d === 0 ? t('dashboard.today') : t('dashboard.daysLeft', { n: d })
}
function dueClass(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  if (d < 0) return 'overdue'
  if (d <= 7) return 'soon'
  return ''
}
function isExpired(s) {
  if (s.billing_type !== 'recurring' || !s.next_renewal_date) return false
  return daysLeft(s) < 0
}
function isSoon(s) {
  if (s.billing_type !== 'recurring' || !s.next_renewal_date) return false
  const d = daysLeft(s)
  return d >= 0 && d <= 7
}

/* ---------- 客户端续费日计算（与后端 billing.add_cycle 对齐） ---------- */
function addMonths(d, months) {
  const base = new Date(d)
  const day = base.getDate()
  const target = new Date(base.getFullYear(), base.getMonth() + months, 1)
  const dim = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate()
  target.setDate(Math.min(day, dim))
  return target
}
function addCycle(dateStr, cycle, count) {
  const n = Math.max(1, count || 1)
  const d = new Date(dateStr)
  if (cycle === 'day') { d.setDate(d.getDate() + n); return d }
  if (cycle === 'week') { d.setDate(d.getDate() + n * 7); return d }
  if (cycle === 'year') return addMonths(d, n * 12)
  return addMonths(d, n)
}
function toISO(d) {
  const x = new Date(d)
  return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`
}

function blank() {
  return {
    id: null, name: '', plan: '', icon: '', amount: 0, currency: 'CNY',
    category_id: null, payment_method_id: null, bundle_id: null, billing_type: 'recurring',
    cycle: 'month', cycle_count: 1, start_date: new Date().toISOString().slice(0, 10),
    next_renewal_date: '', end_date: null, url: '', notes: '', remark: '', ipv4: '', ipv6: '',
    remind_days_before: '7,6,5,4,3,2,1', auto_renew: true, is_active: true,
    show_in_calendar: true, family_members: []
  }
}

let suppressAuto = false
function recomputeNext() {
  if (form.value.billing_type !== 'recurring') { form.value.next_renewal_date = ''; return }
  if (form.value.start_date) {
    form.value.next_renewal_date = toISO(addCycle(form.value.start_date, form.value.cycle, form.value.cycle_count))
  }
}
watch(
  () => [form.value.start_date, form.value.cycle, form.value.cycle_count, form.value.billing_type],
  () => { if (!suppressAuto && showForm.value) recomputeNext() }
)

/* ---------- 分组与拖拽排序 ---------- */
// orderMap: { catKey: [subId, ...] } ; catOrder: [catKey, ...]
const orderMap = reactive({})
const catOrder = ref([])
const NONE = 'none'

function catKeyOf(s) { return s.category_id == null ? NONE : String(s.category_id) }
function catMeta(key) {
  if (key === NONE) return { icon: '🗂️', name: t('sub.uncategorized') }
  const c = categories.value.find((x) => String(x.id) === key)
  return c ? { icon: c.icon || '📁', name: c.name } : { icon: '📁', name: key }
}

function rebuild() {
  Object.keys(orderMap).forEach((k) => delete orderMap[k])
  const byCat = {}
  for (const s of subs.value) {
    const k = catKeyOf(s)
    ;(byCat[k] ||= []).push(s)
  }
  for (const k of Object.keys(byCat)) {
    byCat[k].sort((a, b) => (a.sort - b.sort) || (a.id - b.id))
    orderMap[k] = byCat[k].map((s) => s.id)
  }
  // 分类顺序：用户保存的顺序 → 其余出现的分类 → 未分类置底
  const present = new Set(Object.keys(orderMap))
  const saved = (auth.user?.category_order || []).map(String)
  const order = []
  for (const k of saved) if (present.has(k)) { order.push(k); present.delete(k) }
  const rest = [...present].filter((k) => k !== NONE)
    .sort((a, b) => {
      const ca = categories.value.find((x) => String(x.id) === a)
      const cb = categories.value.find((x) => String(x.id) === b)
      return ((ca?.sort ?? 999) - (cb?.sort ?? 999)) || (Number(a) - Number(b))
    })
  order.push(...rest)
  if (present.has(NONE)) order.push(NONE)
  catOrder.value = order
}

const grouped = computed(() =>
  catOrder.value
    .filter((k) => orderMap[k] && orderMap[k].length)
    .map((k) => {
      const meta = catMeta(k)
      const items = orderMap[k].map((id) => subs.value.find((s) => s.id === id)).filter(Boolean)
      return { key: k, icon: meta.icon, name: meta.name, items }
    })
)

// 拖拽状态
let dragCatKey = null
let dragCard = null
const dragOverCat = ref(null)
const dragOverSub = ref(null)
function clearDrag() { dragCatKey = null; dragCard = null; dragOverCat.value = null; dragOverSub.value = null }

function onCatDragStart(key, e) {
  // 仅当不是从卡片发起时才作为分类拖拽
  if (dragCard) return
  dragCatKey = key
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}
function onCatDragOver(key) { if (dragCatKey && !dragCard) dragOverCat.value = key }
async function onCatDrop(key) {
  if (!dragCatKey || dragCard || dragCatKey === key) return clearDrag()
  const arr = [...catOrder.value]
  const from = arr.indexOf(dragCatKey)
  const to = arr.indexOf(key)
  if (from < 0 || to < 0) return clearDrag()
  arr.splice(to, 0, arr.splice(from, 1)[0])
  catOrder.value = arr
  clearDrag()
  // 持久化（只保存真实分类 id，未分类不存）
  const ids = arr.filter((k) => k !== NONE).map(Number)
  try { await auth.updateMe({ category_order: ids }) } catch { /* ignore */ }
}

function onCardDragStart(catKey, id, e) {
  dragCard = { catKey, id }
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}
function onCardDragOver(catKey, id) {
  if (dragCard && dragCard.catKey === catKey) dragOverSub.value = id
}
async function onCardDrop(catKey, id) {
  if (!dragCard || dragCard.catKey !== catKey || dragCard.id === id) return clearDrag()
  const arr = [...orderMap[catKey]]
  const from = arr.indexOf(dragCard.id)
  const to = arr.indexOf(id)
  if (from < 0 || to < 0) return clearDrag()
  arr.splice(to, 0, arr.splice(from, 1)[0])
  orderMap[catKey] = arr
  clearDrag()
  try { await api.post('/api/subscriptions/reorder', { ordered_ids: arr }) } catch { /* ignore */ }
}

async function load() {
  const params = filter.value ? { billing_type: filter.value } : {}
  const { data } = await api.get('/api/subscriptions', { params })
  subs.value = data
  rebuild()
}
function setFilter(f) { filter.value = f; load() }

function openNew() {
  form.value = blank(); formErr.value = ''; bundleMode.value = 'none'
  newBundleName.value = ''; suggestions.value = []; showForm.value = true
  recomputeNext()
}
function openEdit(s) {
  suppressAuto = true
  form.value = { ...s, next_renewal_date: s.next_renewal_date || '', family_members: s.family_members || [] }
  formErr.value = ''; suggestions.value = []
  bundleMode.value = s.bundle_id ? 'join' : 'none'
  newBundleName.value = ''
  showForm.value = true
  nextTick(() => { suppressAuto = false })
}

function onNameInput() {
  const q = (form.value.name || '').toLowerCase().trim()
  suggestions.value = q.length < 1 ? []
    : iconLib.value.filter((s) => s.name.toLowerCase().includes(q)).slice(0, 6)
}
// 服务库分类 key -> 在用户分类名中查找的关键字
const CAT_KEYWORDS = {
  streaming: 'streaming', music: 'music', ai: 'ai', gaming: 'gaming', vps: 'vps',
  carrier: 'carrier', cloud: 'cloud', software: 'software', domain: 'domain',
  education: 'education', news: 'news', fitness: 'fitness', membership: 'membership'
}
function findCategoryByKey(key) {
  const kw = CAT_KEYWORDS[key]
  if (!kw) return null
  const hit = categories.value.find((c) => (c.name || '').toLowerCase().includes(kw))
  return hit ? hit.id : null
}
const isVpsCategory = computed(() => {
  const c = categories.value.find((x) => x.id === form.value.category_id)
  if (!c) return false
  return (c.name || '').toLowerCase().includes('vps') || (c.name || '').includes('服务器')
})

function pickService(s) {
  form.value.name = s.name
  form.value.icon = s.icon
  if (!form.value.url && s.website) form.value.url = s.website
  // 自动带出分类（按服务库分类映射到用户分类）
  if (s.category) {
    const cid = findCategoryByKey(s.category)
    if (cid) form.value.category_id = cid
  }
  suggestions.value = []
}

function openBrowser() { browserQ.value = ''; showBrowser.value = true }
const groupedLib = computed(() => {
  const q = browserQ.value.toLowerCase().trim()
  const groups = new Map()
  for (const s of iconLib.value) {
    if (q && !s.name.toLowerCase().includes(q)) continue
    const key = s.category || 'other'
    if (!groups.has(key)) groups.set(key, { key, label: s.category_label || key, items: [] })
    groups.get(key).items.push(s)
  }
  return [...groups.values()]
})
function pickFromBrowser(s) { pickService(s); showBrowser.value = false }

function addMember() {
  const v = newMember.value.trim()
  if (v) { form.value.family_members.push(v); newMember.value = '' }
}

async function importIconUrl() {
  if (!iconUrl.value.trim()) return
  try {
    const { data } = await api.post('/api/icons/from-url', { url: iconUrl.value.trim() })
    form.value.icon = data.url; iconUrl.value = ''
  } catch (e) { formErr.value = e.response?.data?.detail || 'Error' }
}
async function uploadIcon(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/api/icons/upload', fd)
  form.value.icon = data.url
}

async function save() {
  formErr.value = ''
  try {
    if (bundleMode.value === 'create' && newBundleName.value.trim()) {
      const { data } = await api.post('/api/bundles', { name: newBundleName.value.trim() })
      form.value.bundle_id = data.id
      bundles.value.push(data)
    } else if (bundleMode.value === 'none') {
      form.value.bundle_id = null
    }
    const payload = { ...form.value }
    if (!payload.next_renewal_date) delete payload.next_renewal_date
    if (payload.id) await api.put(`/api/subscriptions/${payload.id}`, payload)
    else await api.post('/api/subscriptions', payload)
    showForm.value = false
    toast(t('settings.saved'))
    load()
  } catch (e) {
    formErr.value = e.response?.data?.detail || 'Error'
  }
}

/* ---------- 续费 ---------- */
function askRenew(s) { renewTarget.value = s; renewMode.value = 'today' }
const previewToday = computed(() =>
  renewTarget.value ? toISO(addCycle(new Date(), renewTarget.value.cycle, renewTarget.value.cycle_count)) : ''
)
const previewDue = computed(() => {
  if (!renewTarget.value) return ''
  const base = renewTarget.value.next_renewal_date ? new Date(renewTarget.value.next_renewal_date) : new Date()
  return toISO(addCycle(base, renewTarget.value.cycle, renewTarget.value.cycle_count))
})
async function confirmRenew() {
  if (!renewTarget.value || renewing.value) return
  renewing.value = true
  try {
    const { data } = await api.post(`/api/subscriptions/${renewTarget.value.id}/renew`, { mode: renewMode.value })
    toast(t('sub.renewOk', { date: data.next_renewal_date }))
    renewTarget.value = null
    load()
  } catch (e) {
    toast(e.response?.data?.detail || 'Error', 'err')
  } finally {
    renewing.value = false
  }
}

function askDelete(s) { delTarget.value = s; delPwd.value = ''; delErr.value = '' }
async function confirmDelete() {
  if (!delTarget.value || deleting.value || !delPwd.value) return
  deleting.value = true
  delErr.value = ''
  try {
    await api.delete(`/api/subscriptions/${delTarget.value.id}`, { data: { password: delPwd.value } })
    delTarget.value = null
    toast(t('sub.delete'))
    load()
  } catch (e) {
    delErr.value = e.response?.data?.detail || 'Error'
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  const [c, cat, m, b, lib] = await Promise.all([
    api.get('/api/currencies'),
    api.get('/api/categories'),
    api.get('/api/payment-methods'),
    api.get('/api/bundles'),
    api.get('/api/icons/library')
  ])
  currencies.value = c.data
  categories.value = cat.data
  methods.value = m.data
  bundles.value = b.data
  iconLib.value = lib.data
  load()
})
</script>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
h1 { margin-top: 0; }
.bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.seg { display: inline-flex; background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 4px; }
.seg button { border: none; background: transparent; padding: 6px 14px; border-radius: 6px;
  cursor: pointer; color: var(--text-soft); }
.seg button.on { background: var(--primary); color: #fff; }
.drag-hint { font-size: 12px; }
.err { color: var(--danger); font-size: 13px; }
.ico { width: 18px; height: 18px; vertical-align: middle; border-radius: 4px; }
.auto-tip { color: var(--primary); font-size: 11px; }

/* 分类分组 */
.cat-group { margin-bottom: 22px; border-radius: 14px; transition: outline .12s; outline: 2px dashed transparent; }
.cat-group.drop-cat { outline-color: var(--primary); outline-offset: 4px; }
.cat-head { display: flex; align-items: center; gap: 8px; padding: 6px 4px 12px; cursor: grab; }
.cat-head .grip { color: var(--text-soft); cursor: grab; }
.cat-ico { font-size: 18px; }
.cat-name { font-weight: 700; font-size: 16px; }
.cat-count { background: var(--surface-2); color: var(--text-soft); border-radius: 20px;
  padding: 1px 9px; font-size: 12px; }

/* 放大后的订阅卡片 */
.sub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.sub-card { padding: 18px; cursor: grab; position: relative; overflow: hidden;
  transition: transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .25s ease, border-color .2s ease; }
/* 悬停动感：上浮 + 轻微放大 + 渐变高光描边 + 顶部光带扫过 */
.sub-card::after { content: ''; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
  background: linear-gradient(100deg, transparent, color-mix(in srgb, var(--primary) 14%, transparent), transparent);
  transform: skewX(-18deg); opacity: 0; transition: opacity .3s; pointer-events: none; }
.sub-card:hover { transform: translateY(-6px) scale(1.015); box-shadow: var(--shadow-lg);
  border-color: color-mix(in srgb, var(--primary) 45%, var(--border)); }
.sub-card:hover::after { opacity: 1; animation: sheen .8s ease; }
@keyframes sheen { from { left: -60%; } to { left: 130%; } }
.sub-card:hover .sc-ico { transform: scale(1.08) rotate(-3deg); }
.sub-card:active { cursor: grabbing; transform: scale(.99); }
.sub-card.inactive { opacity: .55; }
.sub-card.expired { border-color: var(--danger); box-shadow: 0 0 0 1px var(--danger), var(--shadow); }
.sub-card.soon { border-color: var(--warning); box-shadow: 0 0 0 1px var(--warning), var(--shadow); }
.sub-card.drop-card { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-soft); }
.sc-head { display: flex; align-items: center; gap: 12px; }
.sc-ico { width: 44px; height: 44px; border-radius: 12px; object-fit: contain; border: 1px solid var(--border);
  flex-shrink: 0; background: var(--surface-2); transition: transform .25s cubic-bezier(.2,.8,.2,1); }
.sc-ico.emoji { display: flex; align-items: center; justify-content: center; font-size: 26px; }
.sc-title { flex: 1; min-width: 0; }
.sc-name { font-weight: 600; font-size: 17px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-plan { font-size: 12px; }
.sc-amount { font-size: 28px; font-weight: 700; margin: 14px 0 8px; letter-spacing: -.02em; }
.sc-amount .cur { font-size: 15px; font-weight: 500; }
.sc-amount .cycle { font-size: 14px; font-weight: 500; }
.expired-banner { background: var(--danger); color: #fff; font-size: 12px; font-weight: 600;
  border-radius: 8px; padding: 4px 10px; display: inline-block; margin-bottom: 8px; }
.soon-banner { background: var(--warning); color: #fff; font-size: 12px; font-weight: 600;
  border-radius: 8px; padding: 4px 10px; display: inline-block; margin-bottom: 8px; }
.sc-remark { background: var(--primary-soft); color: var(--primary); border-radius: 8px;
  padding: 6px 10px; font-size: 13px; margin-bottom: 8px; line-height: 1.4;
  word-break: break-word; }
.sc-rows { display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.sc-row { display: flex; justify-content: space-between; gap: 8px; }
.mono { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 12px; }
.sc-row > span:last-child { text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.due.soon { color: var(--warning); font-weight: 600; }
.due.overdue { color: var(--danger); font-weight: 700; }
.tag.one_time { background: #fef3c7; color: #b45309; }
.sc-acts { display: flex; gap: 6px; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); }
.sc-acts .btn { flex: 1; }

/* 续费弹窗单选 */
.opt { display: flex; align-items: flex-start; gap: 10px; border: 1px solid var(--border); border-radius: 10px;
  padding: 12px; margin-top: 10px; cursor: pointer; font-size: 14px; color: var(--text); width: auto; }
.opt.on { border-color: var(--primary); background: var(--primary-soft); }
.opt input { width: auto; margin-top: 3px; }
.opt-d { font-size: 12px; margin-top: 3px; }

/* 表单内复用样式 */
.block { border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 12px; }
.block-t { font-size: 13px; font-weight: 600; color: var(--primary); margin-bottom: 6px; }
.icon-pick { display: flex; align-items: flex-end; }
.ico-lg { width: 40px; height: 40px; border-radius: 8px; object-fit: contain; border: 1px solid var(--border); }
.ico-lg.emoji { display: flex; align-items: center; justify-content: center; font-size: 24px; }
.suggest { position: absolute; z-index: 5; left: 0; right: 0; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); margin-top: 2px; }
.suggest-i { display: flex; align-items: center; gap: 8px; padding: 7px 10px; cursor: pointer; font-size: 14px; }
.suggest-i:hover { background: var(--primary-soft); }
.icon-lib summary { cursor: pointer; font-size: 13px; color: var(--text-soft); }
.lib-grid { display: grid; grid-template-columns: repeat(auto-fill, 34px); gap: 8px; max-height: 140px; overflow: auto; }
.lib-ico { width: 30px; height: 30px; border-radius: 6px; padding: 3px; border: 1px solid var(--border); cursor: pointer; object-fit: contain; }
.lib-ico:hover { border-color: var(--primary); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.chip { background: var(--primary-soft); color: var(--primary); padding: 3px 8px; border-radius: 16px; font-size: 13px; }
.radio-row { gap: 18px; }
.rb { display: flex; align-items: center; gap: 6px; width: auto; margin: 0; font-size: 14px; color: var(--text); }
.rb input { width: auto; }

.browser .modal { width: 560px; }
.lib-group { margin-bottom: 14px; }
.lib-group-t { font-size: 13px; font-weight: 600; color: var(--text-soft); margin-bottom: 8px; }
.svc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.svc { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid var(--border);
  border-radius: 10px; background: var(--surface); cursor: pointer; font-size: 13px; color: var(--text);
  text-align: left; transition: border-color .12s, background .12s; }
.svc:hover { border-color: var(--primary); background: var(--primary-soft); }
.svc-ico { width: 22px; height: 22px; border-radius: 5px; object-fit: contain; flex-shrink: 0; }
.svc span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 720px) {
  .sub-grid { grid-template-columns: 1fr; }
  .sc-name { font-size: 16px; }
}
</style>
