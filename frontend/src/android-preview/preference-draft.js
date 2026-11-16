const clone = value => JSON.parse(JSON.stringify(value))

export function preferenceDraft(user) {
  const draft=clone(user)
  draft.notify_settings={quiet_start:'',quiet_end:'',digest_enabled:false,digest_weekday:0,...draft.notify_settings}
  return draft
}

export function preferencePatch(draft, savedDraft) {
  const patch=clone(draft)
  patch.monthly_budget=draft.monthly_budget==='' ? null : draft.monthly_budget
  if(JSON.stringify(draft.notify_settings)===JSON.stringify(savedDraft.notify_settings))delete patch.notify_settings
  return patch
}
