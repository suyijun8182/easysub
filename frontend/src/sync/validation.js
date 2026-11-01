import { serverUrl } from './transport.js'
export function validateConnection(values, t) {
  const errors = {}
  try { serverUrl(values.server) } catch { errors.server = t('sync.invalidServer') }
  if (!values.username.trim()) errors.username = t('sync.required')
  if (!values.password) errors.password = t('sync.required')
  if (values.otp && !/^\d{6}$/.test(values.otp)) errors.otp = t('sync.invalidOtp')
  return errors
}
