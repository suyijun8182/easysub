import test from 'node:test'
import assert from 'node:assert/strict'
import { billingProgress } from './billing-progress.js'
test('detail progress explains elapsed cycle and clamps dates outside the period',()=>{
 const s={billing_type:'recurring',cycle:'year',cycle_count:1,next_renewal_date:'2027-11-19'}
 assert.equal(billingProgress(s,'2026-11-15'),0)
 assert.equal(billingProgress(s,'2027-11-20'),100)
 assert.equal(billingProgress({...s,cycle:'month',next_renewal_date:'2026-12-15'},'2026-12-01'),53)
 assert.equal(billingProgress({...s,billing_type:'one_time'},'2026-12-01'),null)
 assert.equal(billingProgress({...s,next_renewal_date:'2024-02-29'},'2023-02-28'),0)
})
