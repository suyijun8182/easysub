import { Capacitor, registerPlugin } from '@capacitor/core'
export const isAndroid = () => Capacitor.getPlatform() === 'android'
export const device = registerPlugin('EasySubDevice')

export async function downloadFile(data, name, type = 'application/json') {
  const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  if (isAndroid()) {
    const result = await device.exportFile({ text, name, type })
    if (!result.saved) throw new Error('已取消保存文件')
    return
  }
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a'); a.href = url; a.download = name; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}
