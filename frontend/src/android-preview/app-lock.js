export function createAppLockController({state,native,readStatus,authenticate,saveSettings,exit,now=Date.now}) {
  Object.assign(state,{enabled:true,available:false,reason:'CHECKING',relockMinutes:1,locked:true,covered:true,booting:true,authenticating:false,busy:false,cancels:0,error:'',settingsError:''})
  let hiddenAt=null, active=true, resuming, configuring=Promise.resolve(), waiters=[]
  const canAccess=()=>active && !state.booting && !state.locked && !state.covered && !state.authenticating
  const release=()=>{if(canAccess()){for(const resolve of waiters)resolve();waiters=[]}}
  const whenUnlocked=()=>canAccess()?Promise.resolve():new Promise(resolve=>waiters.push(resolve))
  function uncover() {state.locked=false;state.covered=!active && state.enabled;hiddenAt=active?null:now();release()}
  async function refresh() {
    try {
      const status=native()?await readStatus():{enabled:false,available:false,reason:'PREVIEW',relockMinutes:1}
      Object.assign(state,status);state.booting=false
      if(state.enabled && !state.available){state.locked=true;state.covered=true}
      return true
    } catch {
      state.booting=false;state.available=false;state.reason='ERROR';state.locked=true;state.covered=true
      return false
    }
  }
  async function unlock() {
    if(!state.available || state.cancels>=3 || state.authenticating)return
    state.authenticating=true;state.error=''
    try {await authenticate();state.cancels=0;uncover()}
    catch(error) {state.error=error.code||'UNAVAILABLE';if(state.error==='CANCELED')state.cancels++}
    finally {state.authenticating=false;release()}
  }
  async function start() {
    if(await refresh()) {
      if(!state.enabled)uncover()
      else if(state.available)await unlock()
    }
    return whenUnlocked()
  }
  function background() {
    active=false
    if(state.enabled){state.covered=true;hiddenAt ??= now()}
  }
  function resume() {
    active=true
    if(state.enabled)state.covered=true
    if(resuming)return resuming
    resuming=(async()=>{
      await configuring
      if(!await refresh() || !active)return
      if(!state.enabled)uncover()
      else if(state.available && !state.locked) {
        if(hiddenAt!==null && now()-hiddenAt>=state.relockMinutes*60000){state.locked=true;await unlock()}
        else uncover()
      }
      return whenUnlocked()
    })().finally(()=>{resuming=null})
    return resuming
  }
  async function configure(enabled,relockMinutes) {
    if(!native() || state.busy)return
    state.busy=true;state.settingsError=''
    configuring=(async()=>{
      try {Object.assign(state,await saveSettings({enabled,relockMinutes}));state.cancels=0;uncover()}
      catch(error){state.settingsError=error.code||'UNAVAILABLE'}
      finally{state.busy=false;release()}
    })()
    return configuring
  }
  return {state,start,unlock,background,resume,whenUnlocked,canAccess,configure,refresh,exit}
}
