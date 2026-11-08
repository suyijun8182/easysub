// Isolated, in-memory design preview. Never connects to the production API.
import seed from './seed.json' with { type: 'json' }
import cachedIcons from './cached-icons.json' with { type: 'json' }

const copy = x => JSON.parse(JSON.stringify(x))
const isoToday = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` }
const round = x => Math.round(x * 100) / 100
const csvCell = x => /[",\r\n]/.test(String(x ?? '')) ? `"${String(x).replaceAll('"', '""')}"` : String(x ?? '')
const csv = rows => '\uFEFF' + rows.map(r => r.map(csvCell).join(',')).join('\r\n')
function parseCsv(text) {
  const rows = []; let row = [], cell = '', quoted = false
  text = text.replace(/^\uFEFF/, '')
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (ch === '"') { if (quoted && text[i + 1] === '"') { cell += '"'; i++ } else quoted = !quoted }
    else if (ch === ',' && !quoted) { row.push(cell); cell = '' }
    else if ((ch === '\n' || ch === '\r') && !quoted) {
      if (ch === '\r' && text[i + 1] === '\n') i++
      row.push(cell); rows.push(row); row = []; cell = ''
    } else cell += ch
  }
  if (quoted) throw new Error('CSV 引号未闭合')
  if (cell || row.length) { row.push(cell); rows.push(row) }
  const headers = rows.shift() || []
  if (!headers.includes('name')) throw new Error('CSV 缺少 name 列')
  return rows.filter(r => r.some(Boolean)).map(r => Object.fromEntries(headers.map((h, i) => [h, r[i] || ''])))
}

export function addCycle(value, unit, count = 1) {
  const d = new Date(value + 'T12:00:00Z'); const n = Math.max(1, Number(count) || 1)
  if (unit === 'day' || unit === 'week') d.setUTCDate(d.getUTCDate() + n * (unit === 'week' ? 7 : 1))
  else {
    const day = d.getUTCDate(); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() + n * (unit === 'year' ? 12 : 1))
    const last = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate()
    d.setUTCDate(Math.min(day, last))
  }
  return d.toISOString().slice(0, 10)
}

function normalize(s, today) {
  const out = { name: '', amount: 0, currency: 'CNY', billing_type: 'recurring', cycle: 'month', cycle_count: 1,
    plan: null, icon: null, url: null, notes: null, remark: null, ipv4: null, ipv6: null,
    category_id: null, payment_method_id: null, bundle_id: null, start_date: today, end_date: null,
    next_renewal_date: today, last_renewed_at: null, trial_end: null, cancel_by: null,
    card_last4: '', card_expiry: '', family_members: [], remind_days_before: '7,6,5,4,3,2,1',
    is_active: true, auto_renew: true, show_in_calendar: true, sort: 0, created_at: new Date().toISOString(), ...s }
  if (typeof out.name !== 'string' || !out.name.trim()) throw new Error('请输入服务名称')
  if (!Number.isFinite(Number(out.amount)) || Number(out.amount) < 0) throw new Error('金额必须是非负数')
  if (!['recurring', 'one_time'].includes(out.billing_type) || !['day', 'week', 'month', 'year'].includes(out.cycle)) throw new Error('周期类型无效')
  if (!Number.isInteger(Number(out.cycle_count)) || out.cycle_count < 1) throw new Error('周期数量必须为正整数')
  out.amount = Number(out.amount); out.cycle_count = Number(out.cycle_count)
  if (out.family_members == null) out.family_members = []
  if (!Array.isArray(out.family_members)) throw new Error('家庭成员格式不正确')
  for (const k of ['start_date', 'end_date', 'next_renewal_date', 'trial_end', 'cancel_by', 'last_renewed_at']) {
    if (out[k] && (!/^\d{4}-\d{2}-\d{2}$/.test(out[k]) || Number.isNaN(Date.parse(out[k])) || new Date(out[k]).toISOString().slice(0, 10) !== out[k])) throw new Error('日期格式不正确')
  }
  if (out.card_last4 && !/^\d{4}$/.test(out.card_last4)) throw new Error('卡末四位应为四个数字')
  if (out.card_expiry && !/^(0[1-9]|1[0-2])\/(\d{2}|\d{4})$/.test(out.card_expiry)) throw new Error('卡有效期格式为 MM/YY')
  if (out.billing_type === 'one_time') { out.next_renewal_date = null; out.auto_renew = false }
  else if (!out.next_renewal_date) out.next_renewal_date = today
  return out
}

export function createPreviewStore(fixedDay = null) {
  const currentDay = () => fixedDay ?? isoToday()
  const today = currentDay()
  let next = 1000
  let state = {
    user: { id: 1, username: '本地用户', email: '', is_admin: false, locale: 'zh', theme: 'light', base_currency: 'CNY', monthly_budget: 600, category_order: [], notify_settings: { quiet_start: '22:00', quiet_end: '08:00', digest_enabled: false, digest_weekday: 0 }, totp_enabled: false },
    categories: seed.CATEGORIES.map(([name, icon, color], i) => ({ id: i + 1, name, icon, color, sort: i, is_system: true })),
    payment_methods: seed.PAYMENT_METHODS.map(([name, icon], i) => ({ id: i + 1, name, icon, is_system: true })),
    currencies: seed.CURRENCIES.map(([code, name, symbol]) => ({ code, name, symbol, is_custom: false })),
    rates: { CNY: 1, USD: 1 / 7.2, EUR: 1 / 7.8, HKD: 1 / .92 }, rates_updated_at: null,
    bundles: [{ id: 1, name: '家庭娱乐', note: '家庭共享订阅' }], config: copy(seed.notify), logs: [], notifications: [], subscriptions: []
  }
  const demos = [['Netflix', 98, 1, 'month', 2, '🎬'], ['ChatGPT Plus', 20, 2, 'month', 16, '🤖'], ['iCloud+', 21, 8, 'month', 5, '☁️'], ['Spotify', 38, 7, 'month', 11, '🎵'], ['SIM 保号', 10, 5, 'month', -2, '📱'], ['买断软件', 199, 6, 'year', 0, '🧩']]
  state.subscriptions = demos.map(([name, amount, cat, cycle, days, icon], i) => normalize({ id: i + 1, name, amount, category_id: cat, cycle, icon, currency: name === 'ChatGPT Plus' ? 'USD' : 'CNY', next_renewal_date: addDays(today, days), billing_type: i === 5 ? 'one_time' : 'recurring', remark: name === 'SIM 保号' ? '过期演示：请处理续费' : '设计预览数据', notes: '详细笔记与简短备注独立保存。', payment_method_id: 1, bundle_id: i === 0 ? 1 : null, family_members: i === 0 ? ['家人'] : [], trial_end: i === 1 ? addDays(today, 3) : null }, today))
  for (const sub of state.subscriptions) {
    const service = seed.catalog.find(s => s.name === sub.name || sub.name.startsWith(s.name))
    if (service && cachedIcons.includes(service.slug)) sub.icon = `/preview-icons/${service.slug}.png`
  }
  function log(action, detail) { state.logs.push({ id: next++, action, detail, user: '本地用户', level: 'info', created_at: new Date().toISOString() }) }
  function converted(s) {
    const from = state.rates[s.currency], to = state.rates[state.user.base_currency]
    return from && to ? round(s.amount / from * to) : null
  }
  const out = s => ({ ...copy(s), amount_in_base: converted(s) })
  const catName = s => state.categories.find(c => c.id === s.category_id)?.name || '未分类 / Uncategorized'
  const monthly = s => { const amount = converted(s); return amount == null ? null : amount * ({ day: 30, week: 52 / 12, month: 1, year: 1 / 12 }[s.cycle]) / s.cycle_count }
  function insights() {
    const map = new Map()
    state.subscriptions.filter(s => s.is_active && s.billing_type === 'recurring').forEach(s => map.set(catName(s), (map.get(catName(s)) || 0) + (monthly(s) || 0)))
    const total = [...map.values()].reduce((a, n) => a + n, 0)
    const unconverted = state.subscriptions.filter(s => s.is_active && s.billing_type === 'recurring' && converted(s) == null).length
    return { base_currency: state.user.base_currency, monthly_total: unconverted ? null : round(total), unconverted_count: unconverted, breakdown: [...map].map(([category, value]) => ({ category, monthly: round(value), percent: total ? round(value / total * 100) : 0 })).sort((a, b) => b.monthly - a.monthly) }
  }
  const backup = () => copy({ app: 'EasySub', export_version: 2, exported_at: new Date().toISOString(), user: { ...state.user, notify_config: state.config }, ...Object.fromEntries(['subscriptions', 'categories', 'payment_methods', 'currencies', 'bundles', 'rates', 'rates_updated_at', 'logs', 'notifications'].map(k => [k, state[k]])) })
  function restore(data, replace = false) {
    const today = currentDay()
    if (!data || !Array.isArray(data.subscriptions)) throw new Error('备份缺少 subscriptions，整站文件请先选择用户')
    const candidate = copy(state)
    if (replace) { candidate.subscriptions = []; candidate.notifications = [] }
    const maps = {}
    for (const key of ['categories', 'payment_methods', 'bundles']) {
      maps[key] = new Map()
      if (data[key] != null && !Array.isArray(data[key])) throw new Error('备份关联数据格式错误')
      for (const entity of data[key] || []) {
        if (!entity?.name || typeof entity.name !== 'string') throw new Error('备份实体缺少名称')
        let target = candidate[key].find(e => e.name === entity.name)
        if (!target) { target = { ...copy(entity), id: next++, is_system: false }; candidate[key].push(target) }
        else if (replace) Object.assign(target, { ...copy(entity), id: target.id })
        maps[key].set(entity.id, target.id)
      }
    }
    for (const c of data.currencies || []) if (!candidate.currencies.some(e => e.code === c.code)) {
      candidate.currencies.push({ ...copy(c), is_custom: c.is_custom ?? !seed.CURRENCIES.some(([code]) => code === c.code) })
    }
    let skipped = 0
    const subscriptionIds = new Map()
    for (const source of data.subscriptions) {
      const s = normalize(source, today)
      for (const [field, key] of [['category_id', 'categories'], ['payment_method_id', 'payment_methods'], ['bundle_id', 'bundles']]) s[field] = maps[key].get(source[field]) ?? null
      if (!replace && candidate.subscriptions.some(e => e.name === s.name && e.amount === s.amount && e.currency === s.currency && e.next_renewal_date === s.next_renewal_date)) { skipped++; continue }
      const id = next++
      subscriptionIds.set(source.id, id)
      candidate.subscriptions.push({ ...s, id })
    }
    if (replace && data.user) {
      for (const k of ['locale', 'theme', 'base_currency', 'monthly_budget', 'notify_settings']) if (data.user[k] !== undefined) candidate.user[k] = copy(data.user[k])
      candidate.user.category_order = (data.user.category_order || []).map(id => maps.categories.get(id)).filter(Boolean)
    }
    if (data.user?.notify_config) candidate.config = { ...candidate.config, ...copy(data.user.notify_config) }
    if (data.rates) candidate.rates = { ...candidate.rates, ...copy(data.rates) }
    candidate.rates_updated_at = data.rates_updated_at || candidate.rates_updated_at
    if (replace) {
      candidate.logs = copy(data.logs || []).map(l => ({ ...l, id: next++ }))
      candidate.notifications = copy(data.notifications || []).filter(l => subscriptionIds.has(l.subscription_id)).map(l => ({ ...l, id: next++, subscription_id: subscriptionIds.get(l.subscription_id) }))
    }
    state = candidate; log('backup.import', '恢复预览数据（未写入正式应用）')
    return { ok: true, imported: data.subscriptions.length - skipped, skipped }
  }
  async function request(method, path, body = {}, params = {}) {
    const today = currentDay()
    method = method.toLowerCase(); path = path.split('?')[0]
    if (path === '/api/auth/me') return copy(state.user)
    if (path === '/api/me' && method === 'patch') { Object.assign(state.user, body); log('preferences.update', '更新偏好'); return copy(state.user) }
    if (path === '/api/icons/library') return seed.catalog.map(s => ({ ...s, icon: cachedIcons.includes(s.slug) ? `/preview-icons/${s.slug}.png` : 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#e3f3ec"/><text x="32" y="43" text-anchor="middle" fill="#12805c" font-size="36" font-family="sans-serif">${s.name.slice(0,1).replace(/[<>&]/g,'')}</text></svg>`) }))
    if (path === '/api/notifications/config') {
      if (method === 'put') { state.config = copy(body.config); log('notifications.config', '保存渠道配置（未记录密钥内容）') }
      return { config: copy(state.config), channels: Object.keys(seed.notify) }
    }
    if (path === '/api/notifications/logs') return copy(state.notifications).reverse()
    if (path === '/api/notifications/run-scan') {
      const items = state.subscriptions.filter(s => s.is_active && s.next_renewal_date && (s.remind_days_before || '').split(',').map(Number).includes(dayDiff(today, s.next_renewal_date)))
      for (const s of items) if (!state.notifications.some(n => n.subscription_id === s.id && n.sent_at.startsWith(today))) state.notifications.push({ id: next++, subscription_id: s.id, channel: 'preview', status: 'failed', days_before: dayDiff(today, s.next_renewal_date), sent_at: today + 'T09:00:00', message: `${s.name}：交互预览，不发送系统或外部通知` })
      return { sent: 0, failed: items.length }
    }
    if (path.startsWith('/api/notifications/')) throw new Error('交互预览不发送真实通知或验证第三方凭据；完整配置已保留，等待 Android 实现与测试')
    if (path === '/api/logs') return copy(state.logs.filter(l => !params.after || l.id > params.after)).slice(-(params.limit || 100))
    if (path === '/api/currencies/rate-table') return { base: state.user.base_currency, updated_at: state.rates_updated_at, items: state.currencies.filter(c => c.code !== state.user.base_currency).map(c => ({ ...c, per_unit_in_base: state.rates[c.code] && state.rates[state.user.base_currency] ? round(state.rates[state.user.base_currency] / state.rates[c.code]) : '未缓存' })) }
    if (path.startsWith('/api/currencies/rates/')) throw new Error('预览使用示例汇率，不伪装为实时汇率；可通过自定义币种体验手动汇率')
    if (path === '/api/subscriptions/reorder') { body.ordered_ids.forEach((id, sort) => { const s = state.subscriptions.find(s => s.id === id); if (s) s.sort = sort }); return { ok: true } }
    if (path === '/api/subscriptions/export.csv') return csv([['name', 'plan', 'category', 'amount', 'currency', 'billing_type', 'cycle', 'cycle_count', 'start_date', 'next_renewal_date', 'remark', 'url', 'remind_days_before'], ...state.subscriptions.map(s => [s.name, s.plan, catName(s), s.amount, s.currency, s.billing_type, s.cycle, s.cycle_count, s.start_date, s.next_renewal_date, s.remark, s.url, s.remind_days_before])])
    if (path === '/api/subscriptions/import-csv') {
      const before = copy(state)
      try {
        const rows = parseCsv(body.content)
        for (const row of rows) {
          const cat = row.category ? await request('post', '/api/categories', { name: row.category }) : null
          await request('post', '/api/subscriptions', { ...row, category_id: cat?.id || null, amount: Number(row.amount || 0), cycle_count: Number(row.cycle_count || 1), start_date: row.start_date || today, next_renewal_date: row.next_renewal_date || today })
        }
        return { ok: true, imported: rows.length }
      } catch (e) { state = before; throw e }
    }
    const subMatch = path.match(/^\/api\/subscriptions(?:\/(\d+))?(\/renew)?$/)
    if (subMatch) {
      const id = Number(subMatch[1]); const s = state.subscriptions.find(s => s.id === id)
      if (!id && method === 'get') return state.subscriptions.filter(s => (params.active == null || s.is_active === params.active) && (!params.billing_type || s.billing_type === params.billing_type)).sort((a, b) => a.sort - b.sort || (a.next_renewal_date || '9999').localeCompare(b.next_renewal_date || '9999')).map(out)
      if (!id && method === 'post') { const item = normalize({ ...body, id: next++ }, today); state.subscriptions.push(item); log('subscription.create', `新增「${item.name}」`); return out(item) }
      if (!s) throw new Error('订阅不存在')
      if (subMatch[2]) {
        if (s.billing_type === 'one_time') throw new Error('买断无需续费')
        s.next_renewal_date = addCycle(body.mode === 'due' ? s.next_renewal_date || today : today, s.cycle, s.cycle_count)
        if (body.mode !== 'due') s.start_date = today
        s.last_renewed_at = today; log('subscription.renew', `续费「${s.name}」，${body.mode === 'due' ? '原到期日' : '今天'}起算`); return out(s)
      }
      if (method === 'put') { Object.assign(s, normalize({ ...s, ...body, id: s.id }, today)); log('subscription.update', `编辑「${s.name}」`); return out(s) }
      if (method === 'delete') {
        if (body.password !== 'preview') throw new Error('预览删除确认口令为 preview；正式 App 改用设备认证')
        state.subscriptions = state.subscriptions.filter(x => x.id !== id); state.notifications = state.notifications.filter(x => x.subscription_id !== id); log('subscription.delete', `删除「${s.name}」`); return { ok: true }
      }
      return out(s)
    }
    const entityMatch = path.match(/^\/api\/(categories|payment-methods|bundles|currencies)(?:\/([^/]+))?$/)
    if (entityMatch) {
      const key = entityMatch[1].replace('-', '_'), id = entityMatch[2], list = state[key]
      const identity = key === 'currencies' ? 'code' : 'id'
      const item = list.find(x => String(x[identity]) === id)
      if (method === 'get') return copy(list)
      if (method === 'post') {
        if (!body.name?.trim()) throw new Error('请输入名称')
        const existing = list.find(x => key === 'currencies' ? x.code === body.code?.toUpperCase() : x.name === body.name)
        if (existing) {
          if (key === 'currencies' && Number(body.rate_to_base) > 0) state.rates[existing.code] = Number(body.rate_to_base)
          return copy(existing)
        }
        const obj = { ...copy(body), is_system: false, is_custom: true, ...(key === 'currencies' ? { code: String(body.code || '').toUpperCase() } : { id: next++ }) }
        if (key === 'currencies') { if (!/^[A-Z0-9]{2,8}$/.test(obj.code) || !(body.rate_to_base > 0)) throw new Error('请输入币种代码和有效汇率'); state.rates[obj.code] = Number(body.rate_to_base) }
        list.push(obj); log('entity.create', `新增${body.name}`); return copy(obj)
      }
      if (!item) throw new Error('项目不存在')
      if (method === 'put') { Object.assign(item, body, { [identity]: item[identity] }); return copy(item) }
      if (key === 'currencies' && (state.user.base_currency === id || state.subscriptions.some(s => s.currency === id))) throw new Error('该币种仍在使用，不能删除')
      state[key] = list.filter(x => x !== item)
      const field = { categories: 'category_id', payment_methods: 'payment_method_id', bundles: 'bundle_id' }[key]
      if (field) state.subscriptions.forEach(s => { if (String(s[field]) === id) s[field] = null })
      log('entity.delete', `删除${item.name}并解除关联`); return { ok: true }
    }
    const active = state.subscriptions.filter(s => s.is_active), recurring = active.filter(s => s.billing_type === 'recurring')
    const upcoming = recurring.filter(s => s.next_renewal_date && dayDiff(today, s.next_renewal_date) >= 0 && dayDiff(today, s.next_renewal_date) <= Number(params.days || 30)).sort((a, b) => a.next_renewal_date.localeCompare(b.next_renewal_date))
    if (path === '/api/dashboard') return { base_currency: state.user.base_currency, month_spend: insights().monthly_total, year_spend: round(insights().monthly_total * 12), active_count: active.length, monthly_budget: state.user.monthly_budget, upcoming: upcoming.slice(0, 8).map(out), recent: [...active].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 8).map(out) }
    if (path === '/api/reports/insights') return insights()
    if (path === '/api/reports/ranking') return [...recurring].sort((a, b) => monthly(b) - monthly(a)).map(s => ({ ...out(s), amount_in_base: round(monthly(s) || 0) }))
    if (path === '/api/reports/one-time') return state.subscriptions.filter(s => s.billing_type === 'one_time').map(out)
    if (path === '/api/reports/upcoming') return upcoming.map(out)
    if (path === '/api/reports/expired') return state.subscriptions.filter(s => s.billing_type === 'recurring' && s.next_renewal_date < today).map(out)
    if (path === '/api/reports/recent-payments') return { base_currency: state.user.base_currency, items: state.subscriptions.filter(s => s.last_renewed_at || s.billing_type === 'one_time').map(s => ({ ...out(s), category: catName(s), date: s.last_renewed_at || s.start_date })).sort((a, b) => b.date.localeCompare(a.date)) }
    if (path === '/api/reports/category-detail') {
      const group = type => [...new Set(active.filter(s => s.billing_type === type).map(catName))].map(category => {
        const items = active.filter(s => s.billing_type === type && catName(s) === category)
        return { category, count: items.length, [type === 'recurring' ? 'monthly' : 'total']: round(items.reduce((a, s) => a + (type === 'recurring' ? monthly(s) || 0 : converted(s) || 0), 0)) }
      })
      const recurring = group('recurring'), one_time = group('one_time')
      return { recurring, one_time, recurring_monthly_total: insights().monthly_total, one_time_total: round(one_time.reduce((a, s) => a + s.total, 0)) }
    }
    if (path === '/api/reports/export.csv') return csv([['name', 'currency', 'amount', 'monthly_in_base', 'yearly_in_base'], ...state.subscriptions.map(s => [s.name, s.currency, s.amount, s.billing_type === 'recurring' ? round(monthly(s) || 0) : 0, s.billing_type === 'recurring' ? round((monthly(s) || 0) * 12) : 0])])
    throw new Error(`预览尚未支持该操作：${method} ${path}`)
  }
  log('preview.start', '打开完整功能预览；刷新重置，不连接正式 API')
  function loadState(value) {
    state = copy(value)
    next = Math.max(1000, ...['subscriptions', 'categories', 'payment_methods', 'bundles', 'logs', 'notifications'].flatMap(k => (state[k] || []).map(r => Number(r.id) + 1)))
  }
  return { get state() { return state }, request, backup, restore, loadState }
}

function addDays(day, n) { const d = new Date(day + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10) }
function dayDiff(a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 86400000) }
const to64 = bytes => btoa(Array.from(bytes, b => String.fromCharCode(b)).join(''))
const from64 = str => Uint8Array.from(atob(str), c => c.charCodeAt(0))
async function backupKey(password, salt) {
  if (!globalThis.crypto?.subtle) throw new Error('当前浏览器不是安全环境，无法加密或解密。请在电脑的 http://localhost:5174 预览，或使用安全来源；不会降级为明文导出。')
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 310000, hash: 'SHA-256' }, key, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt'])
}
export async function encryptBackup(data, password) {
  if (!globalThis.crypto?.subtle) throw new Error('当前 HTTP 手机预览不支持加密。请在电脑 http://localhost:5174 使用备份功能；不会导出明文密钥。')
  if (password.length < 8) throw new Error('密码至少 8 位')
  const salt = crypto.getRandomValues(new Uint8Array(16)), iv = crypto.getRandomValues(new Uint8Array(12))
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await backupKey(password, salt), new TextEncoder().encode(JSON.stringify(data)))
  return { app: 'EasySub', format: 'encrypted-preview-v1', salt: to64(salt), iv: to64(iv), ciphertext: to64(new Uint8Array(ciphertext)) }
}
export async function decryptBackup(envelope, password) {
  if (!globalThis.crypto?.subtle) throw new Error('当前 HTTP 手机预览不支持解密，请在电脑 http://localhost:5174 使用备份功能。')
  if (!['encrypted-preview-v1', 'encrypted-full-v1'].includes(envelope.format)) throw new Error('不支持的加密格式')
  try {
    const bytes = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: from64(envelope.iv), ...(envelope.format === 'encrypted-full-v1' ? { additionalData: new TextEncoder().encode(envelope.format) } : {}) }, await backupKey(password, from64(envelope.salt)), from64(envelope.ciphertext))
    return JSON.parse(new TextDecoder().decode(bytes))
  } catch { throw new Error('密码错误或备份文件损坏，原数据未更改') }
}
