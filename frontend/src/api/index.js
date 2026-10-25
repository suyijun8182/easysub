import axios from 'axios'

const api = axios.create({ baseURL: '/' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null
// 登录 / 注册等接口的 401 是业务结果（密码错误、需要两步验证码），交给页面自己显示；
// 不能当成「登录过期」去刷新令牌或整页跳转，否则错误提示和验证码输入框都会随页面刷新消失。
const AUTH_FLOW = /\/api\/auth\/(login|register|refresh|forgot|reset|verify)/
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry && !AUTH_FLOW.test(original.url || '')) {
      original._retry = true
      const rt = localStorage.getItem('refresh_token')
      if (rt) {
        try {
          if (!refreshing) {
            refreshing = axios.post('/api/auth/refresh', { refresh_token: rt })
          }
          const { data } = await refreshing
          refreshing = null
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch (e) {
          refreshing = null
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
