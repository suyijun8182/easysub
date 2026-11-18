const daysInMonth = (year, month) => [31, year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]

export function parseYMD(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error('日期格式不正确')
  const [year, month, day] = value.split('-').map(Number)
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) throw new Error('日期无效')
  return { year, month, day }
}

export function formatYMD({ year, month, day }) {
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

export function todayYMD() {
  const d = new Date()
  return formatYMD({ year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() })
}

export function addCycle(ymd, cycle, count = 1, anchorDay = null) {
  let { year, month, day } = parseYMD(ymd)
  const n = Math.max(1, Math.trunc(Number(count)) || 1)
  if (cycle === 'day' || cycle === 'week') {
    day += n * (cycle === 'week' ? 7 : 1)
    while (day > daysInMonth(year, month)) {
      day -= daysInMonth(year, month)
      if (++month > 12) { month = 1; year++ }
    }
  } else {
    const index = month - 1 + n * (cycle === 'year' ? 12 : 1)
    year += Math.floor(index / 12); month = index % 12 + 1
    day = Math.min(anchorDay || day, daysInMonth(year, month))
  }
  return formatYMD({ year, month, day })
}
