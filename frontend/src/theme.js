// 主题应用：支持固定主题与「跟随系统」(auto)。
// pref 为 'light' | 'dark' | 'ocean' | 'forest' | 'purple' | 'auto'
let listening = false
let currentPref = 'light'

function systemDark() {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

export function applyTheme(pref) {
  currentPref = pref || 'light'
  const resolved = currentPref === 'auto' ? (systemDark() ? 'dark' : 'light') : currentPref
  document.documentElement.setAttribute('data-theme', resolved)
  try { localStorage.setItem('theme', currentPref) } catch { /* ignore */ }
  if (window.matchMedia && !listening) {
    listening = true
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (currentPref === 'auto') applyTheme('auto')
    })
  }
}
