import { defineConfig } from 'vite'
import preview from './vite.android-preview.config.js'

export default defineConfig({
  ...preview,
  plugins: preview.plugins.filter(plugin => plugin.name !== 'local-offline-shell'),
  build: { ...preview.build, outDir: 'dist-android', rollupOptions: { input: 'android-app.html' } }
})
