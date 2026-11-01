import { App } from '@capacitor/app'

export async function setupAndroidLifecycle(router, sync) {
  await App.addListener('appStateChange', ({ isActive }) => { if (isActive) sync() })
  await App.addListener('backButton', () => {
    const dialogs = document.querySelectorAll('[role="dialog"]')
    if (dialogs.length) { dialogs[dialogs.length - 1].dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); return }
    const back = router.options.history.state?.back
    if (back?.startsWith('/') && !back.startsWith('//')) router.back()
    else if (router.currentRoute.value.path.startsWith('/subscriptions/')) router.replace('/subscriptions')
    else if (router.currentRoute.value.path !== '/dashboard') router.replace('/dashboard')
    else App.exitApp()
  })
}
