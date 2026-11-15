import test from 'node:test'
import assert from 'node:assert/strict'
import { groupRenewalDates, placeRenewalDates, timelineLabel } from './timeline-layout.js'
import { renderClass } from './template-test-helper.js'
const row = (id, date) => ({ id, name:`Service ${id}`, amount:12, currency:'CNY', next_renewal_date:date, is_active:true, billing_type:'recurring' })
test('three renewals on the same date render one icon with a +2 badge', async () => {
  const groups=groupRenewalDates([row(1,'2026-11-20'),row(2,'2026-11-20'),row(3,'2026-11-20')],'2026-11-15')
  assert.equal(groups.length,1)
  const html=await renderClass('./MobileTimeline.vue','app-timeline-mark',{placed:placeRenewalDates(groups,260),timelineLabel,select(){}})
  assert.equal((html.match(/<button/g)||[]).length,1)
  assert.match(html,/\+2/)
  for(const s of groups[0].items) assert.ok(html.includes(`${s.name} 2026-11-20 12.00 CNY`))
})
test('adjacent dates keep at least 48px between icon centres using lanes', () => {
  const groups=groupRenewalDates(Array.from({length:10},(_,i)=>row(i,`2026-11-${String(15+i).padStart(2,'0')}`)),'2026-11-15')
  const placed=placeRenewalDates(groups,240)
  for(let i=0;i<placed.length;i++) for(let j=i+1;j<placed.length;j++) assert.ok(Math.hypot(placed[i].x-placed[j].x,(placed[i].lane-placed[j].lane)*48)>=48)
  assert.equal(groupRenewalDates([row(1,'2026-11-14'),row(2,'2026-12-16')],'2026-11-15').length,0)
})
