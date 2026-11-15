export function billingProgress(s, today) {
  if (s.billing_type!=='recurring' || !s.next_renewal_date) return null
  const end=new Date(s.next_renewal_date+'T00:00:00Z'), start=new Date(end), n=Math.max(1,s.cycle_count||1)
  if (s.cycle==='day'||s.cycle==='week') start.setUTCDate(start.getUTCDate()-n*(s.cycle==='week'?7:1))
  else {
    const day=start.getUTCDate();start.setUTCDate(1);start.setUTCMonth(start.getUTCMonth()-n*(s.cycle==='year'?12:1))
    start.setUTCDate(Math.min(day,new Date(Date.UTC(start.getUTCFullYear(),start.getUTCMonth()+1,0)).getUTCDate()))
  }
  if (!today) {const now=new Date();today=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`}
  return Math.round(Math.max(0,Math.min(1,(new Date(today+'T00:00:00Z')-start)/(end-start)))*100)
}
