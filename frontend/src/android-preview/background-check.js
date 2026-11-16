// Hands each complete-sync snapshot to the native background change check
// (docs/android-native-background-check.md). Failures never reach the sync engine.
export function createBackgroundCheck({ native, device, locale, state }) {
  Object.assign(state, { enabled: true, available: native(), busy: false, error: false })
  let lastKey = null
  return {
    state,
    async synced(snapshot) {
      if (!native()) return
      const payload = { server: snapshot.server, access_token: snapshot.tokens?.access_token || '', refresh_token: snapshot.tokens?.refresh_token || '', epoch: snapshot.epoch, cursor: snapshot.cursor, locale: locale() }
      const key = JSON.stringify(payload)
      if (key === lastKey) return
      try { await device.setBackgroundCheck(payload); lastKey = key } catch { lastKey = null }
    },
    async unlinked() {
      lastKey = null
      if (!native()) return
      try { await device.clearBackgroundCheck() } catch { /* Next sync or unlink retries. */ }
    },
    async refresh() {
      if (!native()) return
      try { state.enabled = (await device.backgroundCheckStatus()).enabled; state.error = false } catch { state.error = true }
    },
    async setEnabled(enabled) {
      if (!native() || state.busy) return
      state.busy = true
      try { state.enabled = (await device.setBackgroundCheckEnabled({ enabled })).enabled; state.error = false } catch { state.error = true } finally { state.busy = false }
    }
  }
}
