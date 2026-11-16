const DAY = 86400000
const copy = {
  zh: { renewal:'续费提醒', trial:'试用将结束', cancel:'取消截止', card:'付款卡将到期' },
  en: { renewal:'Renewal reminder', trial:'Trial ending', cancel:'Cancellation deadline', card:'Payment card expiring' },
  ru: { renewal:'Напоминание о продлении', trial:'Пробный период заканчивается', cancel:'Срок отмены', card:'Срок действия карты истекает' }
}
export function parseReminderDays(raw) {
  return [...new Set(String(raw ?? '').split(',').map(s=>s.trim()).filter(s=>/^\d+$/.test(s)).map(Number).filter(Number.isSafeInteger))].sort((a,b)=>a-b)
}
function validDay(day) {
  return /^\d{4}-\d{2}-\d{2}$/.test(day || '') && Number.isFinite(Date.parse(day)) && new Date(day).toISOString().slice(0,10) === day
}
function addDays(day, n) { return new Date(Date.parse(day) + n * DAY).toISOString().slice(0,10) }
function clock(value) {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value || '')) return null
  return Number(value.slice(0,2))*60 + Number(value.slice(3))
}
function zonedClock(timeZone) {
  const formatter=new Intl.DateTimeFormat('en-CA',{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'})
  const parts = time => Object.fromEntries(formatter.formatToParts(new Date(time)).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]))
  const wall = time => { const p=parts(time);return Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second) }
  return {
    day(time) { const p=parts(time); return `${p.year}-${p.month}-${p.day}` },
    instant(day, minute) {
      const target=Date.parse(day)+minute*60000
      const offsets=[...new Set([-36,0,36].map(hours=>{const t=target+hours*3600000;return wall(t)-t}))]
      const candidates=offsets.map(offset=>target-offset)
      const exact=candidates.filter(t=>wall(t)===target)
      // Fold: earliest occurrence. Gap: advance by the DST gap (compatible policy).
      return new Date(exact.length ? Math.min(...exact) : candidates.filter(t=>wall(t)>=target).sort((a,b)=>wall(a)-wall(b))[0])
    }
  }
}
function cardDay(value) {
  const match=/^(0[1-9]|1[0-2])\/(\d{2}|\d{4})$/.exec(String(value || '').replaceAll(' ',''))
  if (!match) return null
  const year=match[2].length===2 ? 2000+Number(match[2]) : Number(match[2])
  if(year<100 || year>9999)return null
  return new Date(Date.UTC(year,Number(match[1]),0)).toISOString().slice(0,10)
}
function hash(key) {
  let h=2166136261
  for(const ch of key) { h^=ch.charCodeAt(0);h=Math.imul(h,16777619) }
  return (h>>>0)%2147483647+1
}

export function reminderSchedule({subscriptions,settings={},now=new Date(),timeZone=Intl.DateTimeFormat().resolvedOptions().timeZone,locale='zh'}) {
  const zone=zonedClock(timeZone), today=zone.day(now), last=addDays(today,60)
  const start=clock(settings?.quiet_start), end=clock(settings?.quiet_end)
  const language=copy[locale] || copy.zh, events=new Map()
  for(const sub of subscriptions) {
    if(!sub.is_active)continue
    const rules=[['trial',sub.trial_end,[3,1,0]],['cancel',sub.cancel_by,[3,1,0]],['card',cardDay(sub.card_expiry),[45,30,7,1,0]]]
    if(sub.billing_type==='recurring')rules.push(['renewal',sub.next_renewal_date,parseReminderDays(sub.remind_days_before)])
    for(const [kind,due,days] of rules) {
      if(!validDay(due))continue
      for(const before of days) {
        if(before>(Date.parse(due)-Date.parse(today))/DAY)continue
        const day=addDays(due,-before)
        if(day<today || day>last)continue
        let atDay=day, minute=540
        const urgent=kind==='renewal' && before<=1
        if(!urgent && start!=null && end!=null && start!==end) {
          const quiet=start<end ? minute>=start && minute<end : minute>=start || minute<end
          if(quiet) { if(start>end && minute>=start)atDay=addDays(day,1);minute=end }
        }
        const at=zone.instant(atDay,minute)
        if(at<=now || zone.day(at)>last)continue
        const key=JSON.stringify([String(sub.id),kind,day])
        events.set(key,{at,title:language[kind],body:`${sub.name} · ${Number(sub.amount).toFixed(2)} ${sub.currency} · ${due}`,extra:{subscriptionId:sub.id,kind}})
      }
    }
  }
  const used=new Set(), rows=[]
  const compare=(a,b)=>a<b ? -1 : a>b ? 1 : 0
  for(const [key,event] of [...events].sort(([a],[b])=>compare(a,b))) {
    let id=hash(key)
    while(used.has(id))id=id===2147483647 ? 1 : id+1
    used.add(id); rows.push({...event,id,_key:key})
  }
  return rows.sort((a,b)=>a.at-b.at || compare(a._key,b._key)).slice(0,64).map(({_key,...event})=>event)
}
