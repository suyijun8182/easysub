export function appearance(user = {}) {
  return {
    locale: ['zh', 'en', 'ru'].includes(user.locale) ? user.locale : 'zh',
    theme: ['light', 'dark', 'ocean', 'forest', 'purple', 'auto'].includes(user.theme) ? user.theme : 'light'
  }
}

export function detailBackTarget(historyState) {
  const path = historyState?.back
  return typeof path === 'string' && path.startsWith('/') && !path.startsWith('//')
    && !/^\/subscriptions\/[^/?#]+/.test(path) ? path : '/subscriptions'
}
