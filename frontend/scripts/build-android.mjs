import { build } from 'vite'
import { copyFile } from 'node:fs/promises'
await build({ configFile: 'vite.android.config.js' })
await copyFile('dist-android/android-app.html', 'dist-android/index.html')
