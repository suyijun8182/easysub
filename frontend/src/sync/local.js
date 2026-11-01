import { edit, emptySync, synchronize, resolveConflict } from './engine.js'
import { createTransport, serverUrl } from './transport.js'
const kinds = { categories: 'categories', 'payment-methods': 'payment_methods', bundles: 'bundles', currencies: 'currencies', subscriptions: 'subscriptions' }
const relations = { category_id: 'categories', payment_method_id: 'payment-methods', bundle_id: 'bundles' }
const clone = value => structuredClone(value)
const prefs = ['base_currency', 'monthly_budget', 'notify_settings', 'category_order']
export async function createLocal(store, storage, changed, transportFactory = createTransport) {
  const defaultSettings = {
    preferences: { ...Object.fromEntries(prefs.map(key => [key, clone(store.state.user[key] ?? null)])), monthly_budget: null, category_order: [] },
    'notification-config': clone(store.state.config)
  }
  let doc = await storage.load()
  if (!doc) {
    const local = clone(store.state)
    Object.assign(local, { subscriptions: [], bundles: [], logs: [], notifications: [], rates: { CNY: 1 }, rates_updated_at: null })
    local.user.monthly_budget = null
    doc = { local, sync: emptySync(), mappings: {}, link: null, tokens: {}, iconCache: {} }
  }
  store.loadState(doc.local)
  let queue = Promise.resolve(), closing = false, syncQueued = null, activeTransport = null
  const serial = fn => { const result = queue.then(fn); queue = result.catch(() => {}); return result }
  const save = async () => { doc.local = clone(store.state); await storage.save(doc); changed() }
  const key = (kind, id) => `${kind}:${id}`
  function identity(kind, id) {
    if (id == null) return null
    return doc.mappings[key(kind, id)] ||= crypto.randomUUID()
  }
  function wire(kind, row) {
    const data = clone(row); delete data.id; delete data.user_id
    if (data.icon) {
      const cached = Object.values(doc.iconCache).find(icon => icon.data === data.icon)
      if (cached) data.icon = cached.source
      else if (doc.link && data.icon.startsWith(doc.link.server + '/')) data.icon = data.icon.slice(doc.link.server.length)
    }
    if (kind === 'subscriptions') {
      delete data.category_name; delete data.monthly_cost; delete data.days_until_renewal
      for (const [field, target] of Object.entries(relations)) data[field] = identity(target, row[field])
    }
    if (kind === 'currencies') { data.rate_base = doc.exchangeBase || 'CNY'; data.rate_to_base = store.state.rates[row.code] ?? null }
    return data
  }
  function collect() {
    const output = {}
    for (const [kind, field] of Object.entries(kinds)) for (const row of store.state[field]) {
      if (row.is_system || (kind === 'currencies' && !row.is_custom)) continue
      output[identity(kind, row.id ?? row.code)] = { kind, data: wire(kind, row), deleted: false }
    }
    for (const kind of ['preferences', 'notification-config']) {
      const record = Object.values(doc.sync.records).find(r => r.kind === kind && !r.deleted)
      if (!record) continue
      const data = kind === 'preferences' ? Object.fromEntries(prefs.map(p => [p, clone(store.state.user[p] ?? null)])) : clone(store.state.config)
      if (kind === 'preferences') data.category_order = (data.category_order || []).map(id => identity('categories', id))
      output[record.id] = { kind, data, deleted: false }
    }
    return output
  }
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b)
  function rememberSettings(oldState) {
    if (doc.link) return
    doc.dirtySettings ||= {}
    if (prefs.some(key => !equal(oldState.user[key], store.state.user[key]))) doc.dirtySettings.preferences = true
    if (!equal(oldState.config, store.state.config)) doc.dirtySettings['notification-config'] = true
  }
  function changes(before) {
    const after = collect()
    for (const [id, row] of Object.entries(after)) if (!equal(before[id], row)) edit(doc.sync, id, row.kind, row.data)
    for (const [id, row] of Object.entries(before)) if (!after[id]) edit(doc.sync, id, row.kind, row.data, true)
  }
  function project() {
    const state = clone(store.state), effective = { ...doc.sync.records }
    state.rates = { [doc.exchangeBase || 'CNY']: 1 }
    for (const op of Object.values(doc.sync.pending)) effective[op.id] = { ...op, readonly: false }
    for (const record of Object.values(effective)) {
      if (record.kind !== 'currencies' || record.deleted) continue
      const prior = doc.mappings[key('currencies', record.data.code)]
      const local = doc.sync.pending[prior]
      if (prior && prior !== record.id && local && !local.deleted) {
        doc.sync.conflicts[prior] = { local: clone(local), server: record, error: 'CURRENCY_CODE_COLLISION：此代码已在网页使用，请将本地币种另存为新代码并调整订阅，或采用网页版本' }
        delete effective[record.id]
      }
    }
    let next = Math.max(1000, ...Object.keys(doc.mappings).map(k => Number(k.split(':')[1]) || 0)) + 1
    const localIds = {}
    for (const [local, id] of Object.entries(doc.mappings)) localIds[id] = local.slice(local.indexOf(':') + 1)
    for (const record of Object.values(effective)) {
      if (!kinds[record.kind]) continue
      if (!localIds[record.id]) {
        const field = kinds[record.kind]
        const existing = state[field].find(row => (record.readonly && row.is_system && row.name === record.data.name) || (record.kind === 'currencies' && row.code === record.data.code))
        const local = record.kind === 'currencies' ? record.data.code : existing?.id || next++
        doc.mappings[key(record.kind, local)] = record.id; localIds[record.id] = String(local)
      }
    }
    for (const field of Object.values(kinds)) state[field] = []
    for (const record of Object.values(effective)) {
      if (record.deleted) continue
      const data = clone(record.data), field = kinds[record.kind]
      if (field) {
        if (record.kind !== 'currencies') data.id = Number(localIds[record.id])
        if (/^\/(static\/icons|api\/icons\/library)\//.test(data.icon || '') && doc.link) data.icon = doc.iconCache[record.id]?.source === data.icon ? doc.iconCache[record.id].data : doc.link.server + data.icon
        if (record.kind === 'subscriptions') for (const [property] of Object.entries(relations)) data[property] = data[property] ? Number(localIds[data[property]]) || null : null
        if (record.kind === 'currencies') { if (data.rate_to_base > 0) state.rates[data.code] = data.rate_to_base; delete data.rate_base; delete data.rate_to_base }
        state[field].push(data)
      } else if (record.kind === 'preferences') {
        data.category_order = (data.category_order || []).map(id => Number(localIds[id])).filter(Boolean)
        Object.assign(state.user, data)
      } else if (record.kind === 'notification-config') state.config = data
    }
    if (doc.link) state.user.username = doc.link.username
    store.loadState(state)
  }
  async function run() {
    if (!doc.link || !doc.sync.enabled || closing) return
    const previous = clone(doc)
    const transport = transportFactory(doc.link.server, doc.tokens)
    activeTransport = transport
    try {
      // Upload local bitmaps before persisting an immutable wire batch.
      for (const op of Object.values(doc.sync.pending)) if (!op.deleted && /^(data:image\/|\/preview-icons\/)/.test(op.data.icon || '') && !doc.sync.inflight?.some(i => i.id === op.id)) {
        const blob = await (await fetch(op.data.icon)).blob(), form = new FormData()
        form.append('file', blob, 'icon.' + (blob.type.split('/')[1] || 'png'))
        const result = await transport.request('/api/icons/upload', { method: 'POST', body: form })
        op.data.icon = result.url
      }
      await synchronize(doc.sync, transport, async () => { project(); await save() })
      for (const record of Object.values(doc.sync.records)) if (!record.deleted && /^\/(static\/icons|api\/icons\/library)\//.test(record.data.icon || '') && doc.iconCache[record.id]?.source !== record.data.icon) {
        try {
          const blob = await transport.request('/api/sync/v1/icons/' + record.id, { asBlob: true })
          if (blob.size > 2 * 1024 * 1024) throw new Error('图标超过 2 MB')
          const data = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(blob) })
          doc.iconCache[record.id] = { source: record.data.icon, data }
        } catch { /* Missing server files retain their source URL and retry next time. */ }
      }
      doc.error = ''; project(); await save()
    } catch (error) {
      if (error.name === 'AbortError') return
      // Persistent progress from successful pages remains valid even if a later request fails.
      doc.error = error.message
      if ([401, 403].includes(error.status) || ['RESET_REQUIRED', 'SYNC_PROTOCOL_UNAVAILABLE'].includes(error.code)) doc.sync.enabled = false
      try { project(); await save() } catch { doc = previous; store.loadState(doc.local); changed(); throw error }
      throw error
    } finally { activeTransport = null }
  }
  const local = {
    get status() { return { ...doc.sync, link: doc.link, error: doc.error, exchange_base: doc.exchangeBase || 'CNY' } },
    request: (...args) => { activeTransport?.abort?.(); return serial(async () => {
      const previous = clone(doc), oldState = clone(store.state), before = collect()
      try { const result = await store.request(...args); rememberSettings(oldState); if (doc.link) changes(before); await save(); return result }
      catch (error) { doc = previous; store.loadState(oldState); changed(); throw error }
    }) },
    restore: (...args) => { activeTransport?.abort?.(); return serial(async () => {
      const previous = clone(doc), oldState = clone(store.state), before = collect()
      if (doc.link && args[0]?.rates && args[0].rate_base !== doc.exchangeBase) throw new Error('备份汇率基准与当前资料库不同或未标明，请先调整备份汇率基准，避免错误换算')
      try { const result = store.restore(...args); rememberSettings(oldState); if (doc.link) changes(before); await save(); return result }
      catch (error) { doc = previous; store.loadState(oldState); throw error }
    }) },
    async test(server, username, password, otp) {
      const tokens = {}, transport = transportFactory(server, tokens)
      Object.assign(tokens, await transport.login(username, password, otp))
      const caps = await transport.capabilities()
      if (caps.protocol !== 1) throw new Error('请先更新服务器以支持同步协议 v1')
      return { server: serverUrl(server), username: caps.username, account_id: caps.account_id, tokens, caps, local_count: store.state.subscriptions.length, web_count: caps.counts?.subscriptions }
    },
    connect: candidate => serial(async () => {
      if (doc.link && (doc.link.server !== candidate.server || doc.link.account_id !== candidate.account_id)) throw new Error('该本地资料库已绑定另一服务器或账号。请先导出备份，使用独立浏览器资料库连接新账号，避免混入原账号数据。')
      if (doc.link && doc.sync.epoch !== candidate.caps.epoch) throw new Error('服务器资料库已恢复，需导出本地备份后重新建立资料库，避免旧记录回写')
      const previous = clone(doc)
      doc.link = { server: candidate.server, username: candidate.username, account_id: candidate.account_id }
      // Vue wraps values assigned to template refs in proxies; keep persisted
      // credentials as plain serializable data so later structuredClone works.
      doc.tokens = { ...candidate.tokens }
      if (!doc.sync.epoch) {
        // Read the account first; never treat absence in the initial snapshot as deletion.
        doc.sync.epoch = candidate.caps.epoch
        const transport = transportFactory(doc.link.server, doc.tokens)
        try {
          let page
          do { page = await transport.changes(doc.sync.epoch, doc.sync.cursor); for (const record of page.changes) doc.sync.records[record.id] = record; doc.sync.cursor = page.next_cursor } while (page.has_more)
          const duplicate = store.state.currencies.find(row => row.is_custom && Object.values(doc.sync.records).some(r => r.kind === 'currencies' && !r.deleted && r.data.code === row.code))
          if (duplicate) throw new Error(`本地自定义币种 ${duplicate.code} 与服务器代码重复，请先备份并调整代码后连接；未合并或上传任何本地资料`)
          const oldBase = doc.exchangeBase || 'CNY', newBase = candidate.caps.exchange_base
          if (oldBase !== newBase && store.state.currencies.some(row => row.is_custom)) {
            const factor = Object.values(doc.sync.records).find(r => r.kind === 'currencies' && !r.deleted && r.data.code === oldBase)?.data.rate_to_base
            if (!(factor > 0)) throw new Error('缺少转换本地自定义汇率所需的服务器基准汇率，请先更新服务器汇率再连接')
            for (const code of Object.keys(store.state.rates)) store.state.rates[code] *= factor
          }
          doc.exchangeBase = newBase
          for (const [kind, field] of Object.entries(kinds)) for (const row of store.state[field]) if (row.is_system || (kind === 'currencies' && !row.is_custom)) {
            const match = Object.values(doc.sync.records).find(r => r.kind === kind && !r.deleted && (kind === 'currencies' ? r.data.code === row.code : r.data.name === row.name))
            if (match) doc.mappings[key(kind, row.id ?? row.code)] = match.id
          }
          for (const [id, row] of Object.entries(collect())) {
            if (kinds[row.kind]) edit(doc.sync, id, row.kind, row.data)
            else if ((doc.dirtySettings?.[row.kind] || !equal(row.data, defaultSettings[row.kind])) && !equal(row.data, doc.sync.records[id].data)) {
              edit(doc.sync, id, row.kind, row.data)
              doc.sync.conflicts[id] = { local: clone(doc.sync.pending[id]), server: clone(doc.sync.records[id]) }
            }
          }
        } catch (error) { doc = previous; store.loadState(doc.local); throw error }
      }
      doc.sync.enabled = true; project(); await save(); await run()
    }),
    sync: () => syncQueued ||= serial(run).finally(() => { syncQueued = null }),
    enable: enabled => serial(async () => { doc.sync.enabled = enabled; await save(); if (enabled) await run() }),
    logout: () => serial(async () => { doc.sync.enabled = false; doc.tokens = {}; await save() }),
    resolve: (id, choice) => serial(async () => {
      if (choice === 'local' && doc.sync.conflicts[id]?.error?.startsWith('CURRENCY_CODE_COLLISION')) throw new Error('同一服务器不能有两个相同币种代码。请另建新代码并修改相关订阅后再采用网页版本；当前本地版本仍已保留。')
      resolveConflict(doc.sync, id, choice); project(); await save(); await run()
    }),
    stop() { closing = true }
  }
  await save()
  return local
}
