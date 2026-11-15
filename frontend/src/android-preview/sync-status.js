export function syncStatus(status) {
  if (!status?.link) return 'local'
  if (status.syncing) return 'syncing'
  if (status.error || Object.keys(status.conflicts || {}).length) return 'failed'
  if (!status.enabled) return 'paused'
  if (!status.last_success || Object.keys(status.pending || {}).length) return 'pending'
  return 'synced'
}
// Server errors arrive in Chinese and are worth showing verbatim to Chinese users;
// transport failures come from the WebView in English and say nothing actionable.
const NETWORK_FAILURE = /failed to fetch|load failed|networkerror|net::err_/i
export const showRawSyncError = (message, locale) => locale === 'zh' && !NETWORK_FAILURE.test(message || '')
