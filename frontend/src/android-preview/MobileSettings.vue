<template>
  <div class="mobile-settings" :aria-busy="busy">
    <div class="page-head"><h1>{{ titles[section] || t('mobile.settings') }}</h1><router-link v-if="section" to="/settings" class="btn ghost">{{ t('mobile.back') }}</router-link></div>
    <p v-if="dirty" class="unsaved-note" role="status">{{ t('mobile.unsavedBadge') }}</p>
    <p v-if="busy" class="settings-busy" role="status">{{ t('sync.busy') }}</p>
    <fieldset :disabled="busy" class="settings-fields">
    <template v-if="!section">
      <section v-for="group in groups" :key="group.title" class="setting-group"><h2>{{ t('mobile.' + group.title) }}</h2><div class="card"><router-link v-for="key in group.items" :key="key" :to="key.startsWith('/') ? key : '/settings/' + key" class="setting-link"><span>{{ titles[key] }}</span><span aria-hidden="true">›</span></router-link></div></section>
      <p class="muted">{{ t('mobile.pendingNative') }}</p>
    </template>
    <form v-else-if="section === 'preferences'" class="card" @submit.prevent="savePrefs">
      <label>{{ t('mobile.language') }}<select v-model="prefs.locale"><option value="zh">中文</option><option value="en">English</option><option value="ru">Русский</option></select></label>
      <label>{{ t('mobile.theme') }}<select v-model="prefs.theme"><option v-for="th in ['light','dark','ocean','forest','purple','auto']" :key="th" :value="th">{{ t('mobile.' + th) }}</option></select></label>
      <label>{{ t('mobile.baseCurrency') }}<select v-model="prefs.base_currency"><option v-for="c in data.currencies" :key="c.code" :value="c.code">{{ c.code }} {{ c.name }}</option></select></label>
      <label>{{ t('mobile.budget') }}<input v-model.number="prefs.monthly_budget" type="number" min="0"></label>
      <button class="btn" type="submit">{{ t('common.save') }}</button>
    </form>
    <form v-else-if="section === 'reminders'" class="card" @submit.prevent="savePrefs">
      <p>{{ text("每项订阅可自定义提前天数。试用与取消截止按提前 3、1、0 天提醒；卡到期检查未来 45 天。") }}</p>
      <label>{{ text("免打扰开始") }}<input v-model="prefs.notify_settings.quiet_start" type="time"></label><label>{{ text("免打扰结束") }}<input v-model="prefs.notify_settings.quiet_end" type="time"></label>
      <label class="check-label"><input type="checkbox" v-model="prefs.notify_settings.digest_enabled">{{ text("启用每周摘要") }}</label>
      <label>{{ text("摘要星期") }}<select v-model.number="prefs.notify_settings.digest_weekday"><option v-for="(d,i) in ['mon','tue','wed','thu','fri','sat','sun']" :value="i" :key="i">{{ t('wk.' + d) }}</option></select></label>
      <p class="muted">{{ text("网页版的今天／明天紧急续费提醒可突破免打扰，手机端需在通知权限页明确告知。系统权限、通知点击跳转及重启恢复待真机实现。") }}</p><button class="btn">{{ text("保存提醒设置") }}</button>
    </form>
    <NotifyChannels v-else-if="section === 'channels'" />
    <template v-else-if="['categories','payment-methods','bundles','currencies'].includes(section)">
      <p class="muted">{{ text("删除分类或支付方式会解除订阅关联，删除捆绑包不会删除订阅；在用币种不能删除。") }}</p>
      <form class="card" @submit.prevent="saveEntity">
        <h2>{{ entity.id ? text("编辑项目") : text("新增项目") }}</h2>
        <label v-if="section === 'currencies'">{{ text("代码") }}<input v-model="entity.code" required maxlength="8"></label>
        <label>{{ text("名称") }}<input v-model="entity.name" required></label>
        <label v-if="['categories','payment-methods'].includes(section)">{{ text("图标 / Emoji") }}<input v-model="entity.icon"></label>
        <label v-if="section === 'categories'">{{ text("颜色") }}<input v-model="entity.color" type="color"></label>
        <label v-if="section === 'categories'">{{ text("顺序") }}<input v-model.number="entity.sort" type="number" min="0"></label>
        <label v-if="section === 'bundles'">{{ text("说明") }}<textarea v-model="entity.note" rows="2"></textarea></label>
        <label v-if="section === 'currencies'">{{ text("货币符号") }}<input v-model="entity.symbol"></label>
        <label v-if="section === 'currencies'">{{ t('sync.rate', { base: preview.isLocal ? localSync.status.exchange_base : 'CNY' }) }}<input v-model.number="entity.rate_to_base" required type="number" min="0.000001" step="any"></label>
        <div class="actions"><button class="btn">{{ entity.id ? text("保存修改") : text("添加") }}</button><button v-if="entity.id" type="button" class="btn ghost" @click="resetEntity">{{ text("取消编辑") }}</button></div>
      </form>
      <section class="card"><div v-for="item in entities" :key="item.id || item.code" class="entity-row"><span class="entity-name">{{ item.icon }} {{ item.code }} {{ item.name }}<small v-if="item.note">{{ item.note }}</small></span><button v-if="section === 'categories'" class="btn ghost" @click="editEntity(item)">{{ text("编辑") }}</button><button class="btn ghost danger" @click="removeEntity(item)">{{ text("删除") }}</button></div></section>
    </template>
    <template v-else-if="section === 'rates'">
      <p class="muted">{{ text("以下为演示缓存汇率，不代表实时市场数据。缺少缓存的币种显示“未缓存”。") }}</p>
      <section class="card"><div v-for="r in rates.items" :key="r.code" class="setting-link"><span>{{ r.code }} {{ r.symbol }}</span><span>1 = {{ r.per_unit_in_base }} {{ rates.base }}</span></div></section>
      <p class="muted">{{ t('mobile.ratesPreview') }}</p><button class="btn" disabled @click="refreshRates">{{ text("刷新汇率") }}</button><router-link class="btn ghost" to="/settings/currencies">{{ text("添加自定义币种与手动汇率") }}</router-link>
    </template>
    <template v-else-if="section === 'backup'">
      <section class="card"><h2>{{ text("完整加密导出") }}</h2><p v-if="!canEncrypt" class="preview-notice">{{ text("手机通过普通 HTTP 局域网访问时，浏览器禁用加密 API。请在电脑 localhost 地址体验加密备份，不会降级导出明文密钥。") }}</p><p class="muted">{{ text("包括全部字段、通知配置、图片数据、偏好、汇率和日志。当前格式仅用于预览，网页版还不能解密此格式。") }}</p>
        <form @submit.prevent="exportEncrypted"><label>{{ text("设置密码") }}<input v-model="password" type="password" minlength="8" required autocomplete="new-password"></label><label>{{ text("确认密码") }}<input v-model="passwordAgain" type="password" minlength="8" required autocomplete="new-password"></label><button class="btn" :disabled="!canEncrypt">{{ text("导出加密备份") }}</button></form><p class="muted">{{ text("密码丢失无法恢复；请勿在设计预览填写真实通知密钥。") }}</p></section>
      <section class="card"><h2>{{ text("导入与恢复") }}</h2><label>{{ text("选择网页 JSON 或预览加密文件") }}<input type="file" accept=".json,application/json" @change="readBackup"></label>
        <form v-if="envelope" @submit.prevent="unlock"><label>{{ text("备份密码") }}<input v-model="importPassword" type="password" required autocomplete="off"></label><button class="btn" :disabled="!canEncrypt">{{ text("解密并预览") }}</button></form>
        <label v-if="fullUsers.length">{{ text("选择一位用户") }}<select v-model.number="selectedUser" @change="selectUser"><option v-for="(u,i) in fullUsers" :value="i" :key="i">{{ u.user?.username || '用户 ' + (i+1) }}</option></select></label>
        <template v-if="incoming"><p class="backup-summary">{{ t('mobile.manage') }}: {{ incoming.subscriptions.length }} · {{ t('mobile.categories') }}: {{ incoming.categories?.length || 0 }} · {{ t('mobile.payments') }}: {{ incoming.payment_methods?.length || 0 }}</p><p v-if="duplicates">{{ locale === 'en' ? 'Possible duplicates' : locale === 'ru' ? 'Возможные повторы' : '检测到重复项' }}: {{ duplicates }}</p><label>{{ text("恢复方式") }}<select v-model="replace"><option :value="false">{{ text("追加（跳过相同项）") }}</option><option :value="true">{{ text("替换（先创建安全副本）") }}</option></select></label><button class="btn" @click="restoreData">{{ text("确认恢复") }}</button></template>
      </section>
      <section class="card"><h2>{{ text("自动备份与安全副本") }}</h2><p class="muted">{{ text("正式 Android 版提供目录授权、定时执行和失败状态。本预览可立即创建内存快照，保留最近 14 份；刷新后清空。") }}</p><button class="btn ghost" @click="makeSnapshot">{{ text("立即创建预览快照") }}</button><div v-for="(b,i) in snapshots" :key="b.time" class="entity-row"><span>{{ b.time }}<small>{{ (JSON.stringify(b.data).length/1024).toFixed(1) }} KB（未编码估算）</small></span><button class="btn ghost" :disabled="!canEncrypt" @click="downloadSnapshot(i)">{{ text("加密下载") }}</button></div></section>
    </template>
    <template v-else-if="section === 'calendar'"><section class="card"><h2>{{ text("导出系统日历文件") }}</h2><p>{{ text("导出有效且允许日历显示的订阅，包含名称、金额、备注与提前一天的提醒。") }}</p><button class="btn" @click="exportIcs">{{ text("导出 ICS") }}</button><p class="muted">{{ text("这是文件快照，后续订阅变更需要重新导出；手机不提供服务器订阅地址。") }}</p></section></template>
    <template v-else-if="section === 'privacy'"><section class="card"><h2>{{ text("设备认证与隐私") }}</h2><p>{{ text("正式 App 使用手机设备认证保护访问，并控制多任务预览中的敏感内容。") }}</p><p class="muted">{{ text("浏览器预览无法验证 Android 设备锁、后台安全存储和系统认证。本页不提供无效的“开启成功”开关。") }}</p><p>{{ text("删除预览数据的确认口令为") }}<b>preview</b>{{ text("。正式 App 将使用删除确认和设备认证，不沿用网站账号密码。") }}</p></section></template>
    <template v-else-if="section === 'about'"><section class="card"><h2>{{ text("EasySub · Android 设计预览") }}</h2><p>{{ text("真实业务页面与演示数据层已接通，未生成正式 APK。") }}</p><a class="btn ghost" href="https://github.com/suyijun8182/easysub/releases" target="_blank" rel="noopener">{{ text("查看 GitHub Releases") }}</a><p class="muted">{{ text("版本检查、签名 APK 升级保留数据、后台任务与外部渠道发送仍需 Android 工程验证。") }}</p></section></template>
    </fieldset>
    <p v-if="message" ref="result" tabindex="-1" class="preview-result" :class="messageKind" :role="messageKind === 'error' ? 'alert' : 'status'">{{ message }}</p>
  </div>
</template>
<script setup>
import { computed, inject, nextTick, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../stores/auth.js'
import NotifyChannels from '../components/NotifyChannels.vue'
import { applyTheme } from '../theme.js'
import { downloadFile } from '../native/device.js'
import { encryptBackup, decryptBackup } from './store.js'
import { settingsCopy } from './settings-copy.js'
import { useUnsavedChanges } from './useUnsavedChanges.js'
const clone = value => JSON.parse(JSON.stringify(value))
const localSync = inject('localSync')
const preview = inject('preview'), route = useRoute(), auth = useAuth(), { t, locale } = useI18n()
const text = value => settingsCopy[value]?.[locale.value] || value
const section = computed(() => route.params.section || '')
const titles = computed(() => Object.fromEntries(Object.entries({ preferences: 'preferences', reminders: 'reminders', channels: 'channels', categories: 'categories', 'payment-methods': 'payments', bundles: 'bundles', currencies: 'currencies', rates: 'rates', backup: 'backup', calendar: 'calendar', privacy: 'privacy', about: 'about', '/notifications': 'noticeLog', '/logs': 'activityLog' }).map(([path,key]) => [path,t('mobile.'+key)])))
const groups = [ { title: 'groupPrefs', items: ['preferences'] }, { title: 'groupRecords', items: ['categories','payment-methods','bundles','currencies','rates'] }, { title: 'groupNotify', items: ['reminders','channels','/notifications','/logs'] }, { title: 'groupData', items: ['backup','calendar','privacy'] }, { title: 'groupAbout', items: ['about'] } ]
const data = ref(preview.state), prefs = ref(clone(preview.state.user)), entity = ref({}), entities = ref([]), rates = ref({ items: [] }), message = ref('')
const password = ref(''), passwordAgain = ref(''), importPassword = ref(''), envelope = ref(null), incoming = ref(null), fullUsers = ref([]), selectedUser = ref(0), replace = ref(false)
// Snapshots contain secrets and live only in this design preview's memory.
const snapshots = inject('snapshots')
const canEncrypt = !!globalThis.crypto?.subtle
const busy = ref(false), result = ref(null)
const messageKind = ref('success'), savedPrefs = ref(JSON.stringify(prefs.value)), savedEntity = ref('')
const dirty = computed(() => ['preferences','reminders'].includes(section.value) ? JSON.stringify(prefs.value) !== savedPrefs.value : ['categories','payment-methods','bundles','currencies'].includes(section.value) && JSON.stringify(entity.value) !== savedEntity.value)
onBeforeRouteLeave(() => !busy.value)
onBeforeRouteUpdate(() => !busy.value)
useUnsavedChanges(() => dirty.value || busy.value, () => t('mobile.unsaved'))
const duplicates = computed(() => (incoming.value?.subscriptions || []).filter(s => data.value.subscriptions.some(x => x.name === s.name && x.amount === s.amount && x.currency === s.currency && x.next_renewal_date === s.next_renewal_date)).length)
function resetEntity() { entity.value = { name: '', icon: '', color: '#12805c', sort: 0, note: '', code: '', symbol: '', rate_to_base: 1 }; savedEntity.value = JSON.stringify(entity.value) }
async function load() { data.value = preview.state; if (['categories','payment-methods','bundles','currencies'].includes(section.value)) entities.value = await preview.request('get', '/api/' + section.value); rates.value = await preview.request('get', '/api/currencies/rate-table') }
async function act(fn) {
  if (busy.value) return
  busy.value = true; message.value = ''; messageKind.value = 'success'
  try { await fn() }
  catch (e) { messageKind.value = 'error'; message.value = e.message; await nextTick(); result.value?.focus() }
  finally { busy.value = false }
}
async function savePrefs() { await act(async () => { await auth.updateMe(clone(prefs.value)); locale.value = prefs.value.locale; applyTheme(prefs.value.theme); savedPrefs.value = JSON.stringify(prefs.value); message.value = t(preview.isLocal ? 'sync.localSaved' : 'mobile.saved'); await load() }) }
function editEntity(item) { entity.value = clone(item); savedEntity.value = JSON.stringify(entity.value); window.scrollTo({ top: 0, behavior: 'instant' }) }
async function saveEntity() { await act(async () => { await preview.request(entity.value.id ? 'put' : 'post', '/api/' + section.value + (entity.value.id ? '/' + entity.value.id : ''), clone(entity.value)); resetEntity(); await load(); message.value = text("已保存") }) }
async function removeEntity(item) { if (!confirm(locale.value === 'en' ? `Delete ${item.name}? Subscriptions will be kept.` : locale.value === 'ru' ? `Удалить ${item.name}? Подписки сохранятся.` : `确认删除「${item.name}」？相关订阅会保留。`)) return; await act(async () => { await preview.request('delete', '/api/' + section.value + '/' + (item.id || item.code)); await load(); message.value = locale.value === 'en' ? 'Deleted; subscriptions kept.' : locale.value === 'ru' ? 'Удалено; подписки сохранены.' : '已删除，关联已安全处理' }) }
async function refreshRates() { await act(() => preview.request('post', '/api/currencies/rates/refresh')) }
const download = downloadFile
async function exportEncrypted() { await act(async () => { if (password.value !== passwordAgain.value) throw new Error(text("两次密码不一致")); await download(await encryptBackup(preview.backup(), password.value), 'easysub-preview-encrypted.json'); password.value = ''; passwordAgain.value = ''; message.value = text("已生成预览加密备份；正式网页尚未支持该格式") }) }
function inspectBackup(value) { if (Array.isArray(value.users)) { fullUsers.value = value.users; selectedUser.value = 0; selectUser() } else { if (!Array.isArray(value.subscriptions)) throw new Error(text("文件缺少 subscriptions")); incoming.value = value } }
async function readBackup(event) { incoming.value = null; envelope.value = null; fullUsers.value = []; importPassword.value = ''; await act(async () => { const file = event.target.files[0]; if (!file) return; if (file.size > 20*1024*1024) throw new Error(text("预览文件上限 20 MB")); const value = JSON.parse(await file.text()); if (value.format) envelope.value = value; else inspectBackup(value) }); event.target.value = '' }
async function unlock() { await act(async () => { inspectBackup(await decryptBackup(envelope.value, importPassword.value)); envelope.value = null; importPassword.value = ''; message.value = text("解密成功，请确认恢复摘要") }) }
function selectUser() { const value = fullUsers.value[selectedUser.value]; if (!Array.isArray(value?.subscriptions)) { incoming.value = null; message.value = text("该用户缺少订阅数据"); return } incoming.value = value }
function makeSnapshot() { messageKind.value = 'success'; snapshots.value.unshift({ time: new Date().toISOString(), data: preview.backup() }); snapshots.value = snapshots.value.slice(0,14); message.value = text("已创建内存安全副本，刷新会清空") }
async function downloadSnapshot(i) { await act(async () => { if (password.value !== passwordAgain.value) throw new Error(text("请先在上方设置并确认加密密码")); await download(await encryptBackup(snapshots.value[i].data, password.value), 'easysub-snapshot-encrypted.json') }) }
async function restoreData() { if (!confirm(locale.value === 'en' ? (replace.value ? 'Replace data? A safety snapshot will be kept first.' : 'Append data and skip duplicates?') : locale.value === 'ru' ? (replace.value ? 'Заменить данные? Сначала будет создан защитный снимок.' : 'Добавить данные, пропуская повторы?') : (replace.value ? '确认替换？会先保留当前内存安全副本。' : '确认追加？相同项将跳过。'))) return; await act(async () => { if (replace.value) makeSnapshot(); const result = await preview.restore(clone(incoming.value), replace.value); await auth.fetchMe(); locale.value = auth.user.locale; prefs.value = clone(auth.user); await load(); incoming.value = null; message.value = locale.value === 'en' ? `Restored ${result.imported}, skipped ${result.skipped}. No system notifications are scheduled in this preview.` : locale.value === 'ru' ? `Восстановлено: ${result.imported}, пропущено: ${result.skipped}. Системные уведомления в макете не планируются.` : `已恢复 ${result.imported} 项，跳过重复 ${result.skipped} 项。预览不安排真实系统通知。` }) }
async function exportIcs() {
  const escape = s => String(s || '').replaceAll('\\', '\\\\').replaceAll('\n', '\\n').replaceAll(',', '\\,').replaceAll(';', '\\;')
  const lines = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//EasySub//Android Preview//CN','CALSCALE:GREGORIAN']
  for (const s of preview.state.subscriptions.filter(s => s.is_active && s.show_in_calendar && s.next_renewal_date)) lines.push('BEGIN:VEVENT',`UID:preview-${s.id}-${s.next_renewal_date}@easysub`,`DTSTAMP:${new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'')}`,`DTSTART;VALUE=DATE:${s.next_renewal_date.replaceAll('-','')}`,`SUMMARY:${escape('续费：'+s.name+' '+s.amount+' '+s.currency)}`,`DESCRIPTION:${escape(s.remark)}`,'BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY',`DESCRIPTION:${escape(s.name)}`,'END:VALARM','END:VEVENT')
  lines.push('END:VCALENDAR'); await act(() => download(lines.join('\r\n')+'\r\n','easysub-preview.ics','text/calendar')); message.value = text("已导出 ICS 文件快照")
}
watch(section, () => { message.value = ''; resetEntity(); load() }, { immediate: true })
</script>
