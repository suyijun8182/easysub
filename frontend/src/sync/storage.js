import { device, isAndroid } from '../native/device.js'

// One encrypted document contains data, cursor and outbox, so they persist atomically.
export async function openStorage() {
  if (isAndroid()) return {
    async load() { const value = await device.load(); return value.json ? JSON.parse(value.json) : null },
    async save(value) { await device.save({ json: JSON.stringify(value) }) }
  }
  if (!globalThis.crypto?.subtle || !globalThis.indexedDB) throw new Error('本地安全存储不可用，请使用 HTTPS 或本机 localhost')
  if (!navigator.locks) throw new Error('此浏览器不支持资料库独占保护，请升级浏览器')
  await new Promise((resolve, reject) => {
    navigator.locks.request('easysub-local-database', { ifAvailable: true }, async lock => {
      if (!lock) { reject(new Error('本地应用已在其他标签页打开，请先关闭该标签页')); return }
      resolve()
      // Keep ownership for the document lifetime, including navigation-cache suspension.
      await new Promise(() => {})
    }).catch(reject)
  })
  const db = await new Promise((resolve, reject) => {
    const request = indexedDB.open('easysub-local-v1', 1)
    request.onupgradeneeded = () => request.result.createObjectStore('data')
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
  const read = key => new Promise((resolve, reject) => {
    const request = db.transaction('data').objectStore('data').get(key)
    request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error)
  })
  const write = (key, value) => new Promise((resolve, reject) => {
    const tx = db.transaction('data', 'readwrite'); tx.objectStore('data').put(value, key)
    tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error || new Error('本地存储事务已取消'))
  })
  let key = await read('key')
  if (!key) { key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']); await write('key', key) }
  return {
    async load() {
      const value = await read('document')
      if (!value) return null
      return JSON.parse(new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: value.iv }, key, value.bytes)))
    },
    async save(value) {
      const iv = crypto.getRandomValues(new Uint8Array(12))
      const bytes = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(JSON.stringify(value)))
      await write('document', { iv, bytes })
    }
  }
}
