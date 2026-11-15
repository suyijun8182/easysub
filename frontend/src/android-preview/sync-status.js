export function syncStatus(status) {
  if (!status?.link) return 'local'
  if (status.syncing) return 'syncing'
  if (status.error || Object.keys(status.conflicts || {}).length) return 'failed'
  if (!status.enabled) return 'paused'
  if (!status.last_success || Object.keys(status.pending || {}).length) return 'pending'
  return 'synced'
}
