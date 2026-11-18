import test from 'node:test'
import assert from 'node:assert/strict'
import { addCycle, todayYMD, parseYMD, formatYMD } from './billing-date.js'

for (const tz of ['America/Los_Angeles', 'Asia/Shanghai']) {
  test(`日历运算不受时区影响：${tz}`, t => {
    const old = process.env.TZ
    try {
      process.env.TZ = tz
      t.mock.timers.enable({ apis: ['Date'], now: Date.parse('2027-02-28T01:00:00+08:00') })
      assert.equal(addCycle('2027-02-28', 'month', 1, 31), '2027-03-31')
      assert.equal(addCycle('2027-01-31', 'month', 1), '2027-02-28')
      assert.equal(addCycle('2028-02-29', 'year', 4, 29), '2032-02-29')
      assert.equal(addCycle('2028-02-28', 'day', 2), '2028-03-01')
      assert.equal(addCycle('2027-12-31', 'week', 1), '2028-01-07')
      assert.equal(formatYMD(parseYMD('2027-03-31')), '2027-03-31')
      assert.throws(() => parseYMD('2027-02-29'))
      const d = new Date()
      assert.equal(todayYMD(), `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`)
      assert.equal(todayYMD(), tz === 'Asia/Shanghai' ? '2027-02-28' : '2027-02-27')
    } finally { if (old === undefined) delete process.env.TZ; else process.env.TZ = old }
  })
}
