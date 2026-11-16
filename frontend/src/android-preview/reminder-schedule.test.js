import test from 'node:test'
import assert from 'node:assert/strict'
import { reminderSchedule, parseReminderDays } from './reminder-schedule.js'

const sub = (patch = {}) => ({ id: 1, name: 'DEVICE_TEST_NOTIFY', amount: 12.5, currency: 'USD', is_active: true, billing_type: 'recurring', next_renewal_date: '2028-03-01', remind_days_before: '1,0', ...patch })
const schedule = (subscriptions = [sub()], patch = {}) => reminderSchedule({ subscriptions, settings: {}, now: new Date('2028-02-28T00:00:00Z'), timeZone: 'UTC', locale: 'en', ...patch })

test('null or partial user notification settings mean no quiet hours',()=>{
  for(const settings of [null,undefined,{}, {quiet_start:'22:00'}, {quiet_end:'08:00'}]) {
    const rows=schedule([sub({billing_type:'one_time',trial_end:'2028-03-02'})],{settings})
    assert.equal(rows.length,3);assert.ok(rows.every(n=>n.at.getUTCHours()===9))
  }
})

test('reminder days accept nonnegative integers, ignore invalid entries and deduplicate', () => {
  assert.deepEqual(parseReminderDays('7, 1,1,0,-2,1.5,no,, +3'), [0,1,7])
  assert.deepEqual(parseReminderDays(null), [])
})
test('renewals cross leap day and month end at local 09:00', () => {
  assert.deepEqual(schedule().map(n => n.at.toISOString()), ['2028-02-29T09:00:00.000Z','2028-03-01T09:00:00.000Z'])
})
test('trial and cancellation use 3,1,0 days even for one-time subscriptions', () => {
  const rows = schedule([sub({ billing_type:'one_time', trial_end:'2028-03-02', cancel_by:'2028-03-02' })])
  assert.equal(rows.length, 6)
  assert.deepEqual([...new Set(rows.map(n=>n.extra.kind))].sort(), ['cancel','trial'])
  assert.deepEqual(rows.filter(n=>n.extra.kind==='trial').map(n=>n.at.toISOString().slice(0,10)), ['2028-02-28','2028-03-01','2028-03-02'])
})
test('card expiry uses last day of month and only 45,30,7,1,0 day milestones', () => {
  const rows = schedule([sub({ billing_type:'one_time', card_expiry:'02/28' })], { now:new Date('2028-01-01T00:00:00Z') })
  assert.deepEqual(rows.map(n=>n.at.toISOString().slice(0,10)), ['2028-01-15','2028-01-30','2028-02-22','2028-02-28','2028-02-29'])
  assert.deepEqual(rows, schedule([sub({ billing_type:'one_time', card_expiry:'02/2028' })], { now:new Date('2028-01-01T00:00:00Z') }))
})
test('quiet hours defer normal events but today/tomorrow renewal bypasses', () => {
  const rows = schedule([sub({ next_renewal_date:'2028-03-02', remind_days_before:'3,1,0', trial_end:'2028-03-02' })], { settings:{quiet_start:'08:00',quiet_end:'11:30'} })
  assert.equal(rows.find(n=>n.extra.kind==='renewal' && n.at.getUTCDate()===28).at.getUTCHours(),11)
  assert.equal(rows.find(n=>n.extra.kind==='renewal' && n.at.getUTCDate()===1).at.getUTCHours(),9)
  assert.ok(rows.filter(n=>n.extra.kind==='trial').every(n=>n.at.getUTCHours()===11 && n.at.getUTCMinutes()===30))
  const overnight = schedule([sub({billing_type:'one_time',trial_end:'2028-02-28'})],{settings:{quiet_start:'22:00',quiet_end:'10:00'}})
  assert.equal(overnight[0].at.getUTCHours(),10)
})
test('specified timezone observes DST rather than adding fixed 24 hour days', () => {
  const rows = schedule([sub({ next_renewal_date:'2028-03-12',remind_days_before:'1,0' })],{now:new Date('2028-03-10T00:00:00Z'),timeZone:'America/Los_Angeles'})
  assert.deepEqual(rows.map(n=>n.at.toISOString()),['2028-03-11T17:00:00.000Z','2028-03-12T16:00:00.000Z'])
})
test('quiet-end inside a spring DST gap advances by the gap and fall fold uses earlier occurrence',()=>{
  const rows=schedule([sub({billing_type:'one_time',trial_end:'2028-03-12'})],{now:new Date('2028-03-11T23:00:00Z'),timeZone:'America/Los_Angeles',settings:{quiet_start:'08:00',quiet_end:'02:30'}})
  assert.equal(rows[0].at.toISOString(),'2028-03-12T10:30:00.000Z')
  const fall=schedule([sub({billing_type:'one_time',trial_end:'2028-11-04'})],{now:new Date('2028-11-04T12:00:00Z'),timeZone:'America/Los_Angeles',settings:{quiet_start:'08:00',quiet_end:'01:30'}})
  assert.equal(fall[0].at.toISOString(),'2028-11-05T08:30:00.000Z')
})
test('past times, invalid dates, inactive subscriptions and beyond 60 calendar days are excluded', () => {
  const now=new Date('2028-01-01T10:00:00Z')
  const rows=schedule([sub({next_renewal_date:'2028-01-01',remind_days_before:'0'}),sub({id:2,next_renewal_date:'2028-03-01',remind_days_before:'0'}),sub({id:3,next_renewal_date:'2028-03-02',remind_days_before:'0'}),sub({id:4,is_active:false}),sub({id:5,next_renewal_date:'2028-02-30'})],{now})
  assert.deepEqual(rows.map(n=>n.extra.subscriptionId),[2])
})
test('stable positive int IDs are order independent and nearest 64 survive', () => {
  const subscriptions=Array.from({length:80},(_,i)=>sub({id:i+1,remind_days_before:'0'}))
  const a=schedule(subscriptions), b=schedule([...subscriptions].reverse())
  assert.deepEqual(a,b);assert.equal(a.length,64)
  assert.equal(new Set(a.map(n=>n.id)).size,64)
  assert.ok(a.every(n=>Number.isInteger(n.id)&&n.id>0&&n.id<=2147483647))
})
test('all three languages contain identity and amount with different event text', () => {
  const titles=[]
  for(const locale of ['zh','en','ru']) {
    const n=schedule([sub()],{locale})[0]; titles.push(n.title)
    assert.match(n.body,/DEVICE_TEST_NOTIFY/);assert.match(n.body,/12.50 USD/)
  }
  assert.equal(new Set(titles).size,3)
})
test('known hash collision is resolved deterministically without overwriting a reminder',()=>{
  const subscriptions=[sub({id:1231,remind_days_before:'0'}),sub({id:81539,remind_days_before:'0'})]
  const rows=schedule(subscriptions)
  assert.equal(rows.length,2);assert.equal(new Set(rows.map(n=>n.id)).size,2)
  assert.deepEqual(rows,schedule([...subscriptions].reverse()))
})
