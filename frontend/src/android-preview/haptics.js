import { isAndroid } from '../native/device.js'

// Device-local preference: vibration hardware belongs to this phone, not the account.
const KEY = 'easysub.haptics'
export const hapticsEnabled = () => { try { return globalThis.localStorage?.getItem(KEY) !== 'off' } catch { return true } }
export function setHapticsEnabled(on) { globalThis.localStorage?.setItem(KEY, on ? 'on' : 'off') }

export function createHaptics({ native = isAndroid, enabled = hapticsEnabled, load = () => import('@capacitor/haptics') } = {}) {
  let plugin
  async function run(play) {
    if (!native() || !enabled()) return false
    try { plugin ||= await load(); await play(plugin); return true } catch { return false }
  }
  return {
    // Wheel snapped to a new value.
    tick: () => run(({ Haptics, ImpactStyle }) => Haptics.impact({ style: ImpactStyle.Light })),
    // Every selected renewal saved.
    success: () => run(({ Haptics, NotificationType }) => Haptics.notification({ type: NotificationType.Success })),
    // Deletion confirmed.
    warning: () => run(({ Haptics, ImpactStyle }) => Haptics.impact({ style: ImpactStyle.Medium }))
  }
}
export const haptics = createHaptics()
