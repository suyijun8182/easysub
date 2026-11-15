const day = date => Date.parse(date + 'T00:00:00Z') / 86400000
export function groupRenewalDates(rows, today, horizon = 30) {
  const groups = new Map()
  for (const s of rows) {
    const offset = day(s.next_renewal_date) - day(today)
    if (!s.is_active || s.billing_type !== 'recurring' || !(offset >= 0 && offset <= horizon)) continue
    const group = groups.get(s.next_renewal_date) || { date:s.next_renewal_date, offset, items:[] }
    group.items.push(s); groups.set(group.date, group)
  }
  return [...groups.values()].sort((a,b) => a.date.localeCompare(b.date))
}
export function placeRenewalDates(groups, width, horizon = 30) {
  const lanes = []
  return groups.map(group => {
    const x = 20 + group.offset / horizon * Math.max(0, width - 40)
    let lane = lanes.findIndex(positions => positions.every(other => Math.abs(other - x) >= 48))
    if (lane < 0) { lane = lanes.length; lanes.push([]) }
    lanes[lane].push(x)
    return { ...group, x, lane }
  })
}
export const timelineLabel = group => group.items.map(s => `${s.name} ${group.date} ${Number(s.amount).toFixed(2)} ${s.currency}`).join('; ')
