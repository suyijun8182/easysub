export function upcomingRenewals(subscriptions, horizon, now = new Date()) {
  const limit = new Date(now)
  limit.setDate(limit.getDate() + horizon)
  const end = `${limit.getFullYear()}-${String(limit.getMonth() + 1).padStart(2, '0')}-${String(limit.getDate()).padStart(2, '0')}`
  return subscriptions.filter(s => s.is_active && s.billing_type === 'recurring' && /^\d{4}-\d{2}-\d{2}$/.test(s.next_renewal_date || '') && s.next_renewal_date <= end)
    .sort((a, b) => a.next_renewal_date.localeCompare(b.next_renewal_date))
}

export async function recordRenewals(ids, mode, request) {
  if (!['today', 'due'].includes(mode)) throw new Error('Invalid renewal mode')
  const applied = [], failed = []
  for (const id of new Set(ids)) {
    try { await request(`/api/subscriptions/${id}/renew`, { mode }); applied.push(id) }
    catch { failed.push(id) }
  }
  return { applied, failed }
}
