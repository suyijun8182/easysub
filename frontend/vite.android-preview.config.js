import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Separate build: never publishes the in-memory preview inside the production site.
export default defineConfig({
  plugins: [vue(), {
    name: 'local-offline-shell',
    generateBundle(_, bundle) {
      const files = ['android-app.html', ...Object.keys(bundle).filter(name => name.startsWith('assets/'))]
      const version = Object.keys(bundle).filter(name => name.endsWith('.js')).join('|')
      let hash = 0; for (const ch of version) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
      this.emitFile({ type: 'asset', fileName: 'local-sw.js', source: `
const CACHE = 'easysub-shell-${hash}';
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(${JSON.stringify(files)}))));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('easysub-shell-') && k !== CACHE).map(k => caches.delete(k))))));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.includes('/api/') || url.pathname.includes('/static/')) return;
  const scope = new URL(self.registration.scope).pathname;
  const local = url.pathname.slice(scope.length);
  if (local !== 'android-app.html' && !local.startsWith('assets/') && !local.startsWith('preview-icons/')) return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })));
});` })
    }
  }],
  build: { target: 'esnext', outDir: 'dist-android-preview', rollupOptions: { input: ['android-features.html', 'android-app.html'] } },
  server: { host: '0.0.0.0', port: 5174, strictPort: true }
})
