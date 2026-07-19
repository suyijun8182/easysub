import { defineStore } from 'pinia'
import api from '../api'
import { applyTheme } from '../theme'

export const useAuth = defineStore('auth', {
  state: () => ({ user: null }),
  getters: { isLoggedIn: () => !!localStorage.getItem('access_token') },
  actions: {
    async login(username, password) {
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const { data } = await api.post('/api/auth/login', form)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      await this.fetchMe()
    },
    async register(username, email, password) {
      // 返回 { status: 'ok' | 'verify' | 'pending', message }，由页面决定后续流程
      const { data } = await api.post('/api/auth/register', { username, email, password })
      return data || { status: 'ok' }
    },
    async verifyEmail(email, code) {
      const { data } = await api.post('/api/auth/verify-email', { email, code })
      return data || { status: 'ok' }
    },
    async fetchMe() {
      const { data } = await api.get('/api/auth/me')
      this.user = data
      localStorage.setItem('locale', data.locale || 'zh')
      applyTheme(data.theme || 'light')
      return data
    },
    async updateMe(patch) {
      const { data } = await api.patch('/api/me', patch)
      this.user = data
      if (patch.theme) applyTheme(patch.theme)
      return data
    },
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      this.user = null
    }
  }
})
