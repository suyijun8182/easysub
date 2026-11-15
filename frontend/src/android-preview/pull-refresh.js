export const PULL_THRESHOLD = 72
// Gestures starting on controls or nested scrollers keep their own behaviour.
const SKIP = 'input, textarea, select, dialog, .inertia-wheel, .desk-rail, [data-no-pull]'

export function createPullRefresh({ status, sync }) {
  let running = null
  return {
    async release(distance) {
      if (distance < PULL_THRESHOLD) return 'cancel'
      if (!status()?.link) return 'local'
      if (running) return 'busy'
      running = Promise.resolve().then(sync)
      try { await running; return 'synced' } catch { return 'failed' } finally { running = null }
    }
  }
}

// Spec pattern (Pointer Events, touch-action note): allow only downward-content
// scrolling while the document sits at the top, so a finger pulling down reaches
// our pointer handlers instead of being cancelled by the browser's own pan.
export function bindPullRefresh(target, { enabled, onMove, onEnd }) {
  const root = document.documentElement
  const atTop = () => (window.scrollY || root.scrollTop) <= 0
  const mark = () => { if (enabled() && atTop()) root.dataset.pullTop = ''; else delete root.dataset.pullTop }
  let start = null, distance = 0
  const reset = () => { start = null; distance = 0 }
  const down = event => { if (event.pointerType === 'touch' && event.isPrimary && enabled() && atTop() && !event.target.closest(SKIP)) { start = event.clientY; distance = 0 } }
  const move = event => { if (start === null || !event.isPrimary) return; distance = Math.max(0, event.clientY - start); onMove(distance) }
  const up = event => { if (start === null || !event.isPrimary) return; const pulled = distance; reset(); onEnd(pulled) }
  const cancel = () => { if (start === null) return; reset(); onMove(0) }
  target.addEventListener('pointerdown', down, { passive: true })
  window.addEventListener('pointermove', move, { passive: true })
  window.addEventListener('pointerup', up, { passive: true })
  window.addEventListener('pointercancel', cancel, { passive: true })
  window.addEventListener('scroll', mark, { passive: true })
  mark()
  return {
    refresh: mark,
    dispose() {
      target.removeEventListener('pointerdown', down)
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up)
      window.removeEventListener('pointercancel', cancel); window.removeEventListener('scroll', mark)
      delete root.dataset.pullTop
    }
  }
}
