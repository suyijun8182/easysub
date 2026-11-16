export function reminderDestination(extra, subscriptions) {
  const sub=subscriptions.find(s=>String(s.id)===String(extra?.subscriptionId))
  return sub ? '/subscriptions/'+encodeURIComponent(sub.id) : '/dashboard'
}

export function createReminderController({native,load,nativeStatus,compute,state,channelName=()=> 'EasySub'}) {
  let plugin, queue=Promise.resolve(), timer
  Object.assign(state,{permission:native()?'loading':'preview',planned:0,error:false})
  const getPlugin=async()=>plugin ||= await load()
  async function refresh() {
    if(!native())return
    const p=await getPlugin(), [status,permission]=await Promise.all([nativeStatus(),p.checkPermissions()])
    state.required=status.required
    state.permission=!status.enabled || permission.display!=='granted' ? 'denied' : status.required ? 'allowed' : 'notRequired'
  }
  async function rebuildNow() {
    if(!native())return
    const rows=compute();state.planned=rows.length
    await refresh()
    const p=await getPlugin(), pending=await p.getPending()
    const owned=pending.notifications.filter(n=>n.extra?.easysubKind==='reminder').map(n=>({id:n.id}))
    if(owned.length)await p.cancel({notifications:owned})
    if(state.permission==='denied') {state.error=false;return}
    await p.createChannel({id:'easysub-reminders-v1',name:channelName(),importance:3,visibility:0})
    if(rows.length)await p.schedule({notifications:rows.map(({at,...row})=>({...row,channelId:'easysub-reminders-v1',isExactNotification:false,schedule:{at},extra:{...row.extra,easysubKind:'reminder'}}))})
    state.error=false
  }
  const rebuild=()=>queue=queue.then(rebuildNow).catch(()=>{state.error=true})
  return {
    rebuild,
    enqueue() {if(!native())return;clearTimeout(timer);timer=setTimeout(rebuild,2000)},
    async refresh() {try{await refresh()}catch{state.error=true}},
    async requestPermission() {
      if(!native())return
      try {await (await getPlugin()).requestPermissions();await rebuild()}catch{state.error=true}
    },
    async listen(handler) {
      if(!native())return
      return (await getPlugin()).addListener('localNotificationActionPerformed',event=>{
        if(event.notification.extra?.easysubKind==='reminder')handler(event.notification.extra)
      })
    }
  }
}
