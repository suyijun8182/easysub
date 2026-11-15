import test from 'node:test'
import assert from 'node:assert/strict'
import { paymentName } from './display-names.js'
import seed from './seed.json' with {type:'json'}
test('system payment names use only the requested language without changing stored names',()=>{
 const row={name:'信用卡 / Credit Card',is_system:true},before=structuredClone(row)
 for(const [locale,label] of Object.entries({zh:'信用卡',en:'Credit Card',ru:'Кредитная карта'})) assert.equal(paymentName(row,locale),label)
 assert.deepEqual(row,before)
 assert.equal(paymentName({...row,is_system:false},'ru'),row.name)
 for(const [name] of seed.PAYMENT_METHODS) for(const locale of ['zh','en','ru']) assert.ok(!paymentName({name,is_system:true},locale).includes(' / '))
})
