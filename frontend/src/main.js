import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './styles/theme.css'
import { applyTheme } from './theme'

// 初始化主题（支持「跟随系统」）
applyTheme(localStorage.getItem('theme') || 'light')

createApp(App).use(createPinia()).use(router).use(i18n).mount('#app')
