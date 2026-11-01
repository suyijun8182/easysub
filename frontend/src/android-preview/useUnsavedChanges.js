import { onBeforeUnmount, onMounted } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'

export function useUnsavedChanges(isDirty, warning) {
  const confirmExit = () => !isDirty() || window.confirm(warning())
  onBeforeRouteLeave(confirmExit)
  onBeforeRouteUpdate(confirmExit)
  const beforeUnload = event => {
    if (!isDirty()) return
    event.preventDefault()
    event.returnValue = ''
  }
  onMounted(() => window.addEventListener('beforeunload', beforeUnload))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
}
