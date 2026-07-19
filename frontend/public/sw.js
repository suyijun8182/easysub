// 省心订阅 EasySub — 简易 Service Worker：缓存应用外壳，支持安装与离线打开。
// 只缓存静态资源；API 请求一律走网络（不缓存动态数据）。
const CACHE = 'easysub-shell-v1'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (e) => {
  const req = e.request
  const url = new URL(req.url)
  // API / 非 GET：直连网络，不缓存
  if (req.method !== 'GET' || url.pathname.startsWith('/api/') || url.pathname.startsWith('/static/')) return
  // 页面导航：网络优先，失败回退缓存的外壳（离线可打开）
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match('/index.html')))
    return
  }
  // 其它静态资源：缓存优先
  e.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone()
      if (res.ok && url.origin === self.location.origin) caches.open(CACHE).then((c) => c.put(req, copy))
      return res
    }).catch(() => hit))
  )
})
