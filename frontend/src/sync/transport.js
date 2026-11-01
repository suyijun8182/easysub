export class SyncError extends Error {
  constructor(message, code, status) { super(message); this.code = code; this.status = status }
}
export function serverUrl(value) {
  const url = new URL(value.trim())
  if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error('请输入完整的服务器网址，不包含账号、查询参数或锚点')
  if (url.protocol !== 'https:' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) throw new Error('同步账号与密钥需要 HTTPS；本机调试可用 localhost')
  return url.href.replace(/\/+$/, '')
}
export function createTransport(server, tokens, fetcher = fetch) {
  const base = serverUrl(server)
  const controller = new AbortController()
  async function raw(path, options = {}, authenticated = true) {
    const { asBlob, ...init } = options
    const response = await fetcher(base + path, { ...init, credentials: 'omit', redirect: 'error', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(20000)]), headers: { ...(authenticated ? { Authorization: `Bearer ${tokens.access_token}` } : {}), ...options.headers } })
    const data = response.ok && asBlob ? await response.blob() : await response.json().catch(() => null)
    if (!response.ok) {
      const detail = data?.detail
      throw new SyncError(typeof detail === 'string' ? detail : detail?.message || `服务器请求失败 (${response.status})`, detail?.code, response.status)
    }
    return data
  }
  let refreshing
  async function request(path, options) {
    try { return await raw(path, options) } catch (error) {
      if (error.status !== 401 || !tokens.refresh_token) throw error
      refreshing ||= raw('/api/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: tokens.refresh_token }) }, false).then(next => Object.assign(tokens, next)).finally(() => { refreshing = null })
      await refreshing
      return raw(path, options)
    }
  }
  return {
    abort: () => controller.abort(),
    request,
    login: (username, password, otp = '') => raw('/api/auth/login', { method: 'POST', body: new URLSearchParams({ username, password, otp, sync_client: 'true' }) }, false),
    async capabilities() {
      let data
      try { data = await request('/api/sync/v1/capabilities') }
      catch (error) {
        if (![404, 405].includes(error.status)) throw error
      }
      if (!data || data.protocol !== 1) throw new SyncError('此服务器尚未提供 App 同步接口，请先升级服务器后重试', 'SYNC_PROTOCOL_UNAVAILABLE')
      return data
    },
    changes: (epoch, cursor) => request(`/api/sync/v1/changes?epoch=${encodeURIComponent(epoch)}&cursor=${cursor}`),
    push: body => request('/api/sync/v1/push', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
    registrationUrl: base + '/login?mode=register'
  }
}
