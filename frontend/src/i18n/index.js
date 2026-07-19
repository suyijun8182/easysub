import { createI18n } from 'vue-i18n'

const zh = {
  app: { title: '省心订阅 EasySub', tagline: '订阅 / 续费 / 保号，一个都不漏' },
  setup: {
    title: '数据库安装向导', subtitle: '首次使用，请配置 MySQL 数据库连接',
    host: '主机地址', port: '端口', user: '用户名', password: '密码', database: '数据库名',
    test: '测试连接', save: '保存并初始化', testing: '测试中...', saving: '初始化中...',
    testOk: '连接成功', testFail: '连接失败', tip: '提示：若数据库也在 Docker Compose 内，主机填服务名（如 db）；否则填 NAS 局域网 IP。',
    done: '配置完成，正在跳转登录...'
  },
  nav: { dashboard: '仪表盘', subscriptions: '订阅管理', calendar: '日历', reports: '报表分析', notifications: '通知中心', notifyConfig: '通知配置', logs: '实时日志', settings: '设置', users: '用户管理', logout: '退出' },
  notifyCfg: {
    title: '通知', save: '保存通知配置', test: '测试通知', saved: '已保存', testOk: '测试通知已发送',
    tgApiBase: 'TG API 反代（可选）', httpProxy: 'HTTP 代理（可选）',
    feishuHint: '飞书群聊的 Chat ID (oc_xxxx)，可通过飞书开放平台获取，支持逗号分隔多个群组。',
    qqGroups: 'GROUP IDS（群聊）', qqUsers: 'USER IDS（私聊）',
    qqHint: '向机器人发送消息后，在实时日志查看 OpenID，填入后 Bot 只对匹配的会话推送。',
    targetUrls: '目标 URLS', noBarkUrl: '尚未配置任何 Bark URL，点右侧添加。',
    barkGroup: '分组 (GROUP)', barkLevel: '通知级别 (LEVEL)',
    host: '主机', port: '端口', username: '用户名', password: '密码', from: '发件人地址 (FROM)', to: '收件人地址 (TO)',
    ppTopic: '群组编码 (TOPIC)', ppChannel: '渠道 (CHANNEL)',
    noWebhookUrl: '尚未配置任何 Webhook URL，点右侧添加。',
    whSecret: '数字签名密钥 (SECRET)', whSecretHint: '若配置，将通过请求头 X-EasySub-Signature 提供 payload 验证。',
    whHeaders: '自定义请求头 (HEADERS)', whTemplate: '文本模板 (TEXT TEMPLATE)',
    whTemplateHint: '支持占位符 text / subject / event / timestamp（各用双花括号包裹，见下方输入框示例）。留空则发送原始文本。',
    whTimeout: '请求超时 (MS)', whRetries: '最大重试次数',
    robotUrl: '机器人 Webhook', signSecret: '加签密钥 (SECRET)', server: '服务器地址', tokenOptional: '令牌（可选）', priority: '优先级',
    serverchanHint: '在 sct.ftqq.com 获取 SendKey（Server酱·Turbo）。',
    wecomHint: '企业微信群 → 添加群机器人 → 复制 Webhook 地址。',
    dingtalkHint: '钉钉群 → 智能群助手 → 添加自定义机器人，安全设置建议用「加签」并把密钥填到上方。',
    discordHint: '频道设置 → 整合 → Webhook → 复制 Webhook URL。',
    slackHint: 'Slack App → Incoming Webhooks → 复制 Webhook URL。',
    ntfyHint: '自建或用公共 ntfy.sh；订阅同名 Topic 即可收到推送。'
  },
  notify: { title: '通知中心', runScan: '立即扫描提醒', empty: '暂无通知记录', sent: '已发送', failed: '失败', daysBefore: '提前天数' },
  rtlog: { title: '实时日志', live: '实时', paused: '已暂停', action: '操作', user: '用户', detail: '详情', time: '时间', empty: '暂无日志', auto: '自动刷新' },
  account: { title: '账号与密码', username: '用户名', email: '邮箱', saveAccount: '保存账号', changePwd: '修改密码', oldPwd: '原密码', newPwd: '新密码', pwdOk: '密码已修改', accountOk: '账号已更新' },
  sys: { title: '系统信息', version: '版本', dbStatus: '数据库', configured: '已连接', serverTime: '服务器时间', timezone: '时区', scanTime: '提醒扫描时间', yourSubs: '我的订阅', totalUsers: '用户总数', totalSubs: '订阅总数' },
  admin: {
    title: '用户管理', username: '用户名', email: '邮箱', role: '角色', admin: '管理员', user: '普通用户',
    status: '状态', active: '正常', disabled: '已禁用', subs: '订阅数', created: '注册时间',
    createUser: '新建用户', password: '密码', makeAdmin: '设为管理员', revokeAdmin: '取消管理员',
    enable: '启用', disable: '禁用', resetPwd: '重置密码', resetPwdPrompt: '输入新密码：',
    confirmDelete: '确认删除该用户及其全部数据？', create: '创建', cancel: '取消',
    approved: '已通过', pending: '待审核', approve: '通过审核', emailUnverified: '邮箱未验证',
    pendingTab: '待审核 ({n})', allTab: '全部用户', noPending: '没有待审核的用户'
  },
  auth: {
    login: '登录', register: '注册', username: '用户名', email: '邮箱', password: '密码',
    loginBtn: '登录', registerBtn: '注册', noAccount: '没有账户？去注册', hasAccount: '已有账户？去登录',
    loginFail: '用户名或密码错误', welcome: '欢迎回来',
    verifyTitle: '邮箱验证', verifyTip: '验证码已发送至 {email}，请查收并填写（10 分钟内有效）',
    code: '验证码', codePh: '6 位数字', verifyBtn: '验证邮箱', backToLogin: '返回登录',
    otp: '两步验证码', otpPh: '验证器 6 位码', forgot: '忘记密码？', forgotTitle: '找回密码', forgotTip: '输入注册邮箱，我们会发送重置码（需管理员已配置 SMTP）。',
    sendCode: '发送重置码', resetTitle: '重置密码', newPassword: '新密码', resetBtn: '重置并登录', resetOk: '密码已重置，请登录',
    pendingTitle: '等待审核', pendingMsg: '注册成功，正在等待管理员审核通过后即可登录。',
    registerOk: '注册成功，请登录'
  },
  dashboard: {
    monthSpend: '本月支出', yearSpend: '年度支出', active: '生效订阅', upcoming: '即将到期', recent: '最近订阅',
    none: '暂无数据', perMonth: '/月', daysLeft: '剩 {n} 天', today: '今天到期',
    overdue: '已过期', byCategory: '分类占比', avgMonth: '平均月支出', expiringSoon: '即将到期', viewAll: '查看全部',
    greeting: '你好，{name} 👋', subtitle: '这是你的订阅总览', catOverview: '分类总览（全部订阅）'
  },
  sub: {
    add: '添加订阅', edit: '编辑订阅', name: '名称', amount: '金额', currency: '货币',
    category: '分类', payment: '付款方式', billingType: '计费类型', recurring: '周期订阅', oneTime: '一次性买断',
    cycle: '周期', cycleCount: '每', day: '天', week: '周', month: '月', year: '年',
    startDate: '开始日期', nextRenewal: '下次续费', endDate: '结束日期', url: '链接', notes: '备注',
    remindDays: '提前提醒(天，逗号分隔)', active: '生效中', autoRenew: '自动续费',
    icon: '图标', save: '保存', cancel: '取消', delete: '删除', renew: '续费', confirmDelete: '确认删除该订阅？',
    uploadIcon: '上传图标', filterAll: '全部', filterRecurring: '周期', filterOneTime: '买断',
    plan: '套餐', planPh: '如 高级版 / 专业版',
    secService: '服务', secPrice: '价格信息', secBilling: '计费信息', secClassify: '分类与支付',
    secFamily: '家庭共享', secBundle: '捆绑包', secExtra: '附加信息', secCalendar: '日历',
    iconLibrary: '图标库', iconUrl: '图标 URL', iconUrlImport: '下载', nameSuggest: '常用服务（点击选择）',
    family: '家庭成员', familyAdd: '添加成员', familyPh: '成员名称',
    bundleNone: '不使用捆绑包', bundleJoin: '加入已有捆绑包', bundleCreate: '创建捆绑包', bundleName: '捆绑包名称',
    showInCalendar: '在日历中显示', website: '官方网站',
    browse: '按分类浏览', browseTitle: '选择服务', searchPh: '搜索服务名…', pickHint: '点击下方服务快速填入名称、图标与官网',
    secTrialCard: '试用 / 付款卡', trialEnd: '试用结束日', cancelBy: '取消截止日', cardLast4: '卡尾号', cardExpiry: '卡有效期 (MM/YY)',
    csvImported: '已导入 {n} 个订阅', perMember: '人均', trialTag: '试用', cancelTag: '待取消', cardTag: '卡',
    renewTitle: '确认续费', renewMsg: '为「{name}」选择续费方式：',
    renewToday: '保号 / 提前续费：从今天起 +1 个周期（重新计周期）',
    renewDue: '常规循环：从原到期日 +1 个周期（不浪费已付时间）',
    renewNext: '续费后下次到期：', renewOk: '已续费，下次到期 {date}', confirm: '确认续费',
    expiredTag: '已过期', soonTag: '即将到期', uncategorized: '未分类', dragHint: '拖动卡片可排序，拖动分类标题可调整分类顺序',
    deleteTitle: '删除订阅', deletePwdTip: '为防止误删，请输入你的登录密码以确认删除「{name}」', pwdPh: '登录密码',
    remark: '个性化备注', remarkPh: '如：家庭主力机 / 香港 CN2（会显示在卡片上）',
    ipLabel: 'IP 地址（选填）', ipv4: 'IPv4', ipv6: 'IPv6'
  },
  calendar: { title: '续费日历', noEvents: '本月无续费', today: '今天', more: '还有 {n} 项' },
  reports: {
    title: '报表分析', overview: '总览', insights: '支出洞察', categoryDetail: '分类明细', recentPayments: '近期付款',
    ranking: '支出排行', oneTime: '永久购买', upcoming: '即将续费', expired: '已过期',
    category: '分类', monthly: '月支出', percent: '占比', total: '月支出合计', empty: '暂无数据',
    exportCsv: '导出 CSV', monthlyTotal: '每月合计', yearlyTotal: '每年合计', byCategory: '分类支出占比', spendTrend: '支出概览',
    recurringSubs: '循环订阅', permanentBuy: '永久购买', count: '数量', amount: '金额', date: '日期', type: '类型',
    permanentTotal: '永久购买总额', recurringMonthly: '循环订阅月支出', noData: '暂无可视化数据'
  },
  settings: {
    title: '设置', language: '语言', theme: '主题', baseCurrency: '基准货币', telegram: 'Telegram 通知',
    tgEnabled: '启用 Telegram 通知', botToken: 'Bot Token', adminId: 'Admin ID',
    apiBase: 'TG API 反代（可选）', proxy: 'HTTP 代理（可选）',
    chatId: 'Chat ID', botStatus: '机器人状态', checkBot: '验证机器人', testSend: '发送测试',
    getUpdates: '获取 Chat ID', save: '保存', saved: '已保存', refreshRates: '刷新汇率', ratesUpdated: '汇率已更新',
    themeLight: '浅色', themeDark: '深色', themeOcean: '海洋', themeForest: '森林', themePurple: '紫罗兰',
    botOk: '机器人正常', botFail: '验证失败', testOk: '测试消息已发送', logs: '通知记录',
    rateTable: '常用货币汇率', rateTip: '1 单位货币兑换为 {base} 的当日金额', updatedAt: '更新于', noRates: '暂无汇率数据，请点击「刷新汇率」'
  },
  backup: {
    title: '数据备份与恢复',
    tip: '把你的订阅及自定义分类/付款方式等导出为 JSON 离线保存；重新部署后导入即可恢复，避免数据丢失。',
    export: '导出备份', import: '导入恢复', replace: '导入前清空现有订阅',
    replaceConfirm: '将先删除你当前的全部订阅，再从备份导入。确定继续？',
    exportOk: '备份已下载', importOk: '已成功导入 {n} 个订阅', importFail: '导入失败：文件格式不正确'
  },
  backupAll: {
    title: '整站备份与恢复（管理员）',
    tip: '导出全部成员的账户与数据为一个 JSON 文件；重新部署后导入即可整站恢复所有用户的订阅、分类等。',
    export: '导出整站备份', import: '导入整站恢复', replace: '每个用户导入前清空其现有订阅',
    importConfirm: '将从整站备份恢复全部成员数据（缺失的账户会自动重建）。确定继续？',
    replaceConfirm: '将先清空每个用户的全部订阅，再从整站备份导入。确定继续？',
    exportOk: '整站备份已下载（{n} 个用户）', importOk: '已恢复 {users} 个用户（新建 {created} 个），共导入 {n} 个订阅'
  },
  cal: {
    title: '日历订阅', tip: '把续费日订阅到 Apple / Google / Outlook 日历，续费日自动进日历并原生提醒。链接为你的私有地址，请勿外泄。',
    get: '获取订阅链接', copy: '复制', reset: '重置链接', copied: '已复制到剪贴板', resetOk: '链接已重置（旧链接失效）'
  },
  autobk: {
    title: '本地自动备份', tip: '系统每天凌晨自动把整站数据导出到服务器 data/backups 目录，多一层保险。',
    run: '立即备份一次', keep: '保留最近 {n} 份', none: '暂无自动备份文件'
  },
  remind: {
    title: '提醒与预算', budget: '月度预算', budgetPh: '0 或留空 = 不限',
    quietStart: '免打扰开始', quietEnd: '免打扰结束',
    quietHint: '免打扰时段内仅暂缓非紧急提醒；到期当天/次日的提醒仍会照常发送。',
    digest: '每周汇总推送', over: '已超预算', budgetLeft: '预算剩余'
  },
  wk: { mon: '周一', tue: '周二', wed: '周三', thu: '周四', fri: '周五', sat: '周六', sun: '周日' },
  sec: {
    title: '安全', twofa: '两步验证 (2FA)', on: '已开启', off: '未开启', enable: '开启', disable: '关闭',
    confirmEnable: '确认开启', scanTip: '用 Google Authenticator / 1Password 等扫码，或手动输入密钥：',
    enabledOk: '两步验证已开启', disabledOk: '两步验证已关闭', enterPwd: '请输入登录密码以关闭两步验证',
    apiTokens: 'API Token', tokenName: 'Token 名称', tokenOnce: '请立即复制并妥善保管，仅显示一次：',
    neverUsed: '未使用', revokeConfirm: '确定吊销该 Token？使用它的脚本将立即失效。'
  },
  upd: {
    title: '版本与更新', check: '检查更新', newVersion: '发现新版本 v{v}', isLatest: '已是最新版本', failed: '检查失败（无法连接 GitHub）',
    howto: '升级方式（数据不丢，自动迁移）：', view: '查看更新内容', banner: '发现新版本 v{v}，前往设置查看升级方式',
    backupTip: '升级前建议先在「数据备份」导出一份。'
  },
  common: { loading: '加载中...', save: '保存', actions: '操作', status: '状态', date: '日期', confirm: '确认', cancel: '取消', close: '关闭' }
}

const en = {
  app: { title: 'EasySub', tagline: 'Never miss a renewal again' },
  setup: {
    title: 'Database Setup', subtitle: 'First run — configure your MySQL connection',
    host: 'Host', port: 'Port', user: 'User', password: 'Password', database: 'Database',
    test: 'Test connection', save: 'Save & initialize', testing: 'Testing...', saving: 'Initializing...',
    testOk: 'Connected', testFail: 'Connection failed', tip: 'Tip: if MySQL runs in the same Compose, use the service name (e.g. db) as host; otherwise use the NAS LAN IP.',
    done: 'Done, redirecting to login...'
  },
  nav: { dashboard: 'Dashboard', subscriptions: 'Subscriptions', calendar: 'Calendar', reports: 'Reports', notifications: 'Notifications', notifyConfig: 'Notify Channels', logs: 'Live Logs', settings: 'Settings', users: 'Users', logout: 'Logout' },
  notifyCfg: {
    title: 'Notifications', save: 'Save config', test: 'Test', saved: 'Saved', testOk: 'Test notification sent',
    tgApiBase: 'TG API proxy (optional)', httpProxy: 'HTTP proxy (optional)',
    feishuHint: 'Feishu chat ID (oc_xxxx) from the open platform; comma-separate multiple groups.',
    qqGroups: 'GROUP IDS', qqUsers: 'USER IDS',
    qqHint: 'After messaging the bot, find the OpenID in Live Logs; the bot only pushes to matching chats.',
    targetUrls: 'Target URLs', noBarkUrl: 'No Bark URL yet — click Add on the right.',
    barkGroup: 'Group', barkLevel: 'Level',
    host: 'host', port: 'port', username: 'Username', password: 'Password', from: 'From', to: 'To',
    ppTopic: 'Topic', ppChannel: 'Channel',
    noWebhookUrl: 'No Webhook URL yet — click Add on the right.',
    whSecret: 'Signing secret', whSecretHint: 'If set, payload is signed via the X-EasySub-Signature header.',
    whHeaders: 'Custom headers', whTemplate: 'Text template',
    whTemplateHint: 'Placeholders: text / subject / event / timestamp (wrap each in double curly braces, see the input example). Empty = raw text.',
    whTimeout: 'Timeout (ms)', whRetries: 'Max retries',
    robotUrl: 'Robot Webhook', signSecret: 'Sign secret', server: 'Server', tokenOptional: 'Token (optional)', priority: 'Priority',
    serverchanHint: 'Get your SendKey at sct.ftqq.com (ServerChan Turbo).',
    wecomHint: 'WeCom group → add group robot → copy the Webhook URL.',
    dingtalkHint: 'DingTalk group → add custom robot; recommended security: sign, put the secret above.',
    discordHint: 'Channel settings → Integrations → Webhooks → copy the Webhook URL.',
    slackHint: 'Slack App → Incoming Webhooks → copy the Webhook URL.',
    ntfyHint: 'Self-hosted or public ntfy.sh; subscribe to the same topic to receive pushes.'
  },
  notify: { title: 'Notification Center', runScan: 'Run scan now', empty: 'No notifications yet', sent: 'Sent', failed: 'Failed', daysBefore: 'Days before' },
  rtlog: { title: 'Live Logs', live: 'Live', paused: 'Paused', action: 'Action', user: 'User', detail: 'Detail', time: 'Time', empty: 'No logs', auto: 'Auto refresh' },
  account: { title: 'Account & Password', username: 'Username', email: 'Email', saveAccount: 'Save account', changePwd: 'Change password', oldPwd: 'Old password', newPwd: 'New password', pwdOk: 'Password changed', accountOk: 'Account updated' },
  sys: { title: 'System Info', version: 'Version', dbStatus: 'Database', configured: 'Connected', serverTime: 'Server time', timezone: 'Timezone', scanTime: 'Scan time', yourSubs: 'My subscriptions', totalUsers: 'Total users', totalSubs: 'Total subscriptions' },
  admin: {
    title: 'User Management', username: 'Username', email: 'Email', role: 'Role', admin: 'Admin', user: 'User',
    status: 'Status', active: 'Active', disabled: 'Disabled', subs: 'Subs', created: 'Created',
    createUser: 'New user', password: 'Password', makeAdmin: 'Make admin', revokeAdmin: 'Revoke admin',
    enable: 'Enable', disable: 'Disable', resetPwd: 'Reset password', resetPwdPrompt: 'New password:',
    confirmDelete: 'Delete this user and all their data?', create: 'Create', cancel: 'Cancel',
    approved: 'Approved', pending: 'Pending', approve: 'Approve', emailUnverified: 'Email not verified',
    pendingTab: 'Pending ({n})', allTab: 'All users', noPending: 'No users awaiting approval'
  },
  auth: {
    login: 'Login', register: 'Register', username: 'Username', email: 'Email', password: 'Password',
    loginBtn: 'Sign in', registerBtn: 'Sign up', noAccount: 'No account? Register', hasAccount: 'Have an account? Login',
    loginFail: 'Wrong username or password', welcome: 'Welcome back',
    verifyTitle: 'Verify email', verifyTip: 'A code was sent to {email}. Enter it below (valid 10 min).',
    code: 'Code', codePh: '6 digits', verifyBtn: 'Verify', backToLogin: 'Back to login',
    otp: '2FA code', otpPh: '6-digit code', forgot: 'Forgot password?', forgotTitle: 'Reset password', forgotTip: 'Enter your email; we\'ll send a reset code (requires admin SMTP).',
    sendCode: 'Send reset code', resetTitle: 'Reset password', newPassword: 'New password', resetBtn: 'Reset & log in', resetOk: 'Password reset, please log in',
    pendingTitle: 'Awaiting approval', pendingMsg: 'Registered. Waiting for an admin to approve your account.',
    registerOk: 'Registered, please sign in'
  },
  dashboard: {
    monthSpend: 'This Month', yearSpend: 'This Year', active: 'Active', upcoming: 'Upcoming', recent: 'Recent',
    none: 'No data', perMonth: '/mo', daysLeft: '{n} days left', today: 'Due today',
    overdue: 'Overdue', byCategory: 'By category', avgMonth: 'Avg / month', expiringSoon: 'Expiring soon', viewAll: 'View all',
    greeting: 'Hi, {name} 👋', subtitle: 'Here is your subscription overview', catOverview: 'All subscriptions by category'
  },
  sub: {
    add: 'Add', edit: 'Edit', name: 'Name', amount: 'Amount', currency: 'Currency',
    category: 'Category', payment: 'Payment', billingType: 'Billing', recurring: 'Recurring', oneTime: 'One-time',
    cycle: 'Cycle', cycleCount: 'Every', day: 'day', week: 'week', month: 'month', year: 'year',
    startDate: 'Start', nextRenewal: 'Next renewal', endDate: 'End', url: 'URL', notes: 'Notes',
    remindDays: 'Remind days before (comma)', active: 'Active', autoRenew: 'Auto renew',
    icon: 'Icon', save: 'Save', cancel: 'Cancel', delete: 'Delete', renew: 'Renew', confirmDelete: 'Delete this subscription?',
    uploadIcon: 'Upload icon', filterAll: 'All', filterRecurring: 'Recurring', filterOneTime: 'One-time',
    plan: 'Plan', planPh: 'e.g. Premium / Pro',
    secService: 'Service', secPrice: 'Price', secBilling: 'Billing', secClassify: 'Category & Payment',
    secFamily: 'Family sharing', secBundle: 'Bundle', secExtra: 'Extra', secCalendar: 'Calendar',
    iconLibrary: 'Icon library', iconUrl: 'Icon URL', iconUrlImport: 'Import', nameSuggest: 'Common services (click to pick)',
    family: 'Members', familyAdd: 'Add member', familyPh: 'Member name',
    bundleNone: 'No bundle', bundleJoin: 'Join existing bundle', bundleCreate: 'Create bundle', bundleName: 'Bundle name',
    showInCalendar: 'Show in calendar', website: 'Website',
    browse: 'Browse by category', browseTitle: 'Pick a service', searchPh: 'Search services…', pickHint: 'Click a service to fill name, icon and website',
    secTrialCard: 'Trial / Card', trialEnd: 'Trial ends', cancelBy: 'Cancel by', cardLast4: 'Card last 4', cardExpiry: 'Card expiry (MM/YY)',
    csvImported: 'Imported {n} subscriptions', perMember: 'per person', trialTag: 'trial', cancelTag: 'cancel', cardTag: 'card',
    renewTitle: 'Confirm renewal', renewMsg: 'Choose how to renew "{name}":',
    renewToday: 'Keep-alive / early: +1 cycle from today (restart the cycle)',
    renewDue: 'Regular recurring: +1 cycle from current due date (no paid time lost)',
    renewNext: 'Next due after renewal:', renewOk: 'Renewed, next due {date}', confirm: 'Confirm',
    expiredTag: 'Expired', soonTag: 'Due soon', uncategorized: 'Uncategorized', dragHint: 'Drag cards to reorder; drag a category header to reorder categories',
    deleteTitle: 'Delete subscription', deletePwdTip: 'To prevent mistakes, enter your login password to delete "{name}"', pwdPh: 'Login password',
    remark: 'Personal note', remarkPh: 'e.g. main box / HK CN2 (shown on card)',
    ipLabel: 'IP address (optional)', ipv4: 'IPv4', ipv6: 'IPv6'
  },
  calendar: { title: 'Renewal Calendar', noEvents: 'No renewals this month', today: 'Today', more: '+{n} more' },
  reports: {
    title: 'Reports', overview: 'Overview', insights: 'Insights', categoryDetail: 'Category detail', recentPayments: 'Recent payments',
    ranking: 'Ranking', oneTime: 'Permanent', upcoming: 'Upcoming', expired: 'Expired',
    category: 'Category', monthly: 'Monthly', percent: 'Share', total: 'Monthly total', empty: 'No data',
    exportCsv: 'Export CSV', monthlyTotal: 'Monthly total', yearlyTotal: 'Yearly total', byCategory: 'Spend by category', spendTrend: 'Spend overview',
    recurringSubs: 'Recurring', permanentBuy: 'Permanent', count: 'Count', amount: 'Amount', date: 'Date', type: 'Type',
    permanentTotal: 'Permanent total', recurringMonthly: 'Recurring monthly', noData: 'No chart data'
  },
  settings: {
    title: 'Settings', language: 'Language', theme: 'Theme', baseCurrency: 'Base currency', telegram: 'Telegram',
    tgEnabled: 'Enable Telegram notifications', botToken: 'Bot Token', adminId: 'Admin ID',
    apiBase: 'TG API proxy (optional)', proxy: 'HTTP proxy (optional)',
    chatId: 'Chat ID', botStatus: 'Bot status', checkBot: 'Verify bot', testSend: 'Send test',
    getUpdates: 'Get Chat ID', save: 'Save', saved: 'Saved', refreshRates: 'Refresh rates', ratesUpdated: 'Rates updated',
    themeLight: 'Light', themeDark: 'Dark', themeOcean: 'Ocean', themeForest: 'Forest', themePurple: 'Purple',
    botOk: 'Bot OK', botFail: 'Verify failed', testOk: 'Test sent', logs: 'Logs',
    rateTable: 'Currency rates', rateTip: 'Today value of 1 unit in {base}', updatedAt: 'Updated', noRates: 'No rate data, click "Refresh rates"'
  },
  backup: {
    title: 'Backup & Restore',
    tip: 'Export your subscriptions and custom categories/payment methods as JSON. After a redeploy, import it back to restore and avoid data loss.',
    export: 'Export backup', import: 'Import & restore', replace: 'Clear existing subscriptions first',
    replaceConfirm: 'This will delete all your current subscriptions before importing. Continue?',
    exportOk: 'Backup downloaded', importOk: 'Imported {n} subscriptions', importFail: 'Import failed: invalid file'
  },
  backupAll: {
    title: 'Full Site Backup & Restore (Admin)',
    tip: 'Export every member\'s account and data as one JSON file. After a redeploy, import it to restore all users\' subscriptions, categories and more.',
    export: 'Export full backup', import: 'Import full backup', replace: 'Clear each user\'s subscriptions first',
    importConfirm: 'This restores all members\' data from a full-site backup (missing accounts are recreated). Continue?',
    replaceConfirm: 'This clears every user\'s subscriptions before importing from the full backup. Continue?',
    exportOk: 'Full backup downloaded ({n} users)', importOk: 'Restored {users} users ({created} created), imported {n} subscriptions'
  },
  cal: {
    title: 'Calendar subscription', tip: 'Subscribe renewal dates in Apple / Google / Outlook Calendar with native reminders. This is your private URL — keep it secret.',
    get: 'Get subscribe URL', copy: 'Copy', reset: 'Reset URL', copied: 'Copied to clipboard', resetOk: 'URL reset (old one revoked)'
  },
  autobk: {
    title: 'Local auto-backup', tip: 'The server exports a full-site snapshot to data/backups every night — an extra safety net.',
    run: 'Back up now', keep: 'Keeps last {n}', none: 'No auto-backup files yet'
  },
  remind: {
    title: 'Reminders & budget', budget: 'Monthly budget', budgetPh: '0 or empty = no limit',
    quietStart: 'Quiet from', quietEnd: 'Quiet to',
    quietHint: 'Quiet hours only defer non-urgent reminders; due-today/tomorrow reminders still send.',
    digest: 'Weekly digest', over: 'Over budget', budgetLeft: 'Budget left'
  },
  wk: { mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun' },
  sec: {
    title: 'Security', twofa: 'Two-factor (2FA)', on: 'enabled', off: 'off', enable: 'Enable', disable: 'Disable',
    confirmEnable: 'Confirm', scanTip: 'Scan with Google Authenticator / 1Password, or enter the key manually:',
    enabledOk: '2FA enabled', disabledOk: '2FA disabled', enterPwd: 'Enter your password to disable 2FA',
    apiTokens: 'API Tokens', tokenName: 'Token name', tokenOnce: 'Copy and store it now — shown only once:',
    neverUsed: 'never used', revokeConfirm: 'Revoke this token? Scripts using it will stop working.'
  },
  upd: {
    title: 'Version & updates', check: 'Check for updates', newVersion: 'New version v{v} available', isLatest: 'You are on the latest version', failed: 'Check failed (cannot reach GitHub)',
    howto: 'How to upgrade (data preserved, auto-migrated):', view: 'View changes', banner: 'New version v{v} available — see Settings to upgrade',
    backupTip: 'Export a backup from Data backup before upgrading.'
  },
  common: { loading: 'Loading...', save: 'Save', actions: 'Actions', status: 'Status', date: 'Date', confirm: 'Confirm', cancel: 'Cancel', close: 'Close' }
}

const ru = {
  app: { title: 'EasySub', tagline: 'Не пропустите ни одного продления' },
  setup: {
    title: 'Настройка базы данных', subtitle: 'Первый запуск — укажите подключение MySQL',
    host: 'Хост', port: 'Порт', user: 'Пользователь', password: 'Пароль', database: 'База данных',
    test: 'Проверить', save: 'Сохранить и инициализировать', testing: 'Проверка...', saving: 'Инициализация...',
    testOk: 'Подключено', testFail: 'Ошибка подключения', tip: 'Подсказка: если MySQL в том же Compose — укажите имя сервиса (например db); иначе IP NAS в локальной сети.',
    done: 'Готово, переход ко входу...'
  },
  nav: { dashboard: 'Панель', subscriptions: 'Подписки', calendar: 'Календарь', reports: 'Отчёты', notifications: 'Уведомления', notifyConfig: 'Каналы', logs: 'Логи', settings: 'Настройки', users: 'Пользователи', logout: 'Выход' },
  notifyCfg: {
    title: 'Уведомления', save: 'Сохранить', test: 'Тест', saved: 'Сохранено', testOk: 'Тестовое уведомление отправлено',
    tgApiBase: 'TG API прокси (опц.)', httpProxy: 'HTTP прокси (опц.)',
    feishuHint: 'Chat ID Feishu (oc_xxxx); несколько групп — через запятую.',
    qqGroups: 'GROUP IDS', qqUsers: 'USER IDS',
    qqHint: 'После сообщения боту найдите OpenID в логах; бот пишет только в совпавшие чаты.',
    targetUrls: 'Целевые URL', noBarkUrl: 'Нет URL Bark — нажмите «Добавить».',
    barkGroup: 'Группа', barkLevel: 'Уровень',
    host: 'хост', port: 'порт', username: 'Логин', password: 'Пароль', from: 'Отправитель', to: 'Получатели',
    ppTopic: 'Topic', ppChannel: 'Канал',
    noWebhookUrl: 'Нет URL Webhook — нажмите «Добавить».',
    whSecret: 'Ключ подписи', whSecretHint: 'Если задан, payload подписывается заголовком X-EasySub-Signature.',
    whHeaders: 'Заголовки', whTemplate: 'Шаблон текста',
    whTemplateHint: 'Плейсхолдеры: text / subject / event / timestamp (в двойных фигурных скобках, см. пример в поле). Пусто = исходный текст.',
    whTimeout: 'Таймаут (мс)', whRetries: 'Повторы',
    robotUrl: 'Webhook робота', signSecret: 'Секрет подписи', server: 'Сервер', tokenOptional: 'Токен (опц.)', priority: 'Приоритет',
    serverchanHint: 'Получите SendKey на sct.ftqq.com (ServerChan Turbo).',
    wecomHint: 'Группа WeCom → добавить робота → скопировать Webhook URL.',
    dingtalkHint: 'Группа DingTalk → добавить робота; рекомендуется подпись, укажите секрет выше.',
    discordHint: 'Настройки канала → Интеграции → Вебхуки → скопировать URL.',
    slackHint: 'Slack App → Incoming Webhooks → скопировать URL.',
    ntfyHint: 'Свой или публичный ntfy.sh; подпишитесь на тот же topic.'
  },
  notify: { title: 'Центр уведомлений', runScan: 'Запустить проверку', empty: 'Нет уведомлений', sent: 'Отправлено', failed: 'Ошибка', daysBefore: 'За дней' },
  rtlog: { title: 'Логи в реальном времени', live: 'Онлайн', paused: 'Пауза', action: 'Действие', user: 'Польз.', detail: 'Детали', time: 'Время', empty: 'Нет логов', auto: 'Автообновление' },
  account: { title: 'Аккаунт и пароль', username: 'Логин', email: 'Эл. почта', saveAccount: 'Сохранить', changePwd: 'Сменить пароль', oldPwd: 'Старый пароль', newPwd: 'Новый пароль', pwdOk: 'Пароль изменён', accountOk: 'Аккаунт обновлён' },
  sys: { title: 'О системе', version: 'Версия', dbStatus: 'База данных', configured: 'Подключено', serverTime: 'Время сервера', timezone: 'Часовой пояс', scanTime: 'Время проверки', yourSubs: 'Мои подписки', totalUsers: 'Всего польз.', totalSubs: 'Всего подписок' },
  admin: {
    title: 'Пользователи', username: 'Логин', email: 'Эл. почта', role: 'Роль', admin: 'Админ', user: 'Пользователь',
    status: 'Статус', active: 'Активен', disabled: 'Отключён', subs: 'Подписки', created: 'Создан',
    createUser: 'Новый', password: 'Пароль', makeAdmin: 'Сделать админом', revokeAdmin: 'Снять админа',
    enable: 'Включить', disable: 'Отключить', resetPwd: 'Сбросить пароль', resetPwdPrompt: 'Новый пароль:',
    confirmDelete: 'Удалить пользователя и все его данные?', create: 'Создать', cancel: 'Отмена',
    approved: 'Одобрен', pending: 'Ожидает', approve: 'Одобрить', emailUnverified: 'Почта не подтверждена',
    pendingTab: 'Ожидают ({n})', allTab: 'Все', noPending: 'Нет ожидающих одобрения'
  },
  auth: {
    login: 'Вход', register: 'Регистрация', username: 'Логин', email: 'Эл. почта', password: 'Пароль',
    loginBtn: 'Войти', registerBtn: 'Создать', noAccount: 'Нет аккаунта? Регистрация', hasAccount: 'Есть аккаунт? Войти',
    loginFail: 'Неверный логин или пароль', welcome: 'С возвращением',
    verifyTitle: 'Подтверждение почты', verifyTip: 'Код отправлен на {email}. Введите его ниже (действует 10 мин).',
    code: 'Код', codePh: '6 цифр', verifyBtn: 'Подтвердить', backToLogin: 'Назад ко входу',
    otp: 'Код 2FA', otpPh: '6-значный код', forgot: 'Забыли пароль?', forgotTitle: 'Сброс пароля', forgotTip: 'Введите email; отправим код сброса (нужен SMTP у админа).',
    sendCode: 'Отправить код', resetTitle: 'Сброс пароля', newPassword: 'Новый пароль', resetBtn: 'Сбросить и войти', resetOk: 'Пароль сброшен, войдите',
    pendingTitle: 'Ожидание одобрения', pendingMsg: 'Регистрация завершена. Ожидайте одобрения администратора.',
    registerOk: 'Регистрация завершена, войдите'
  },
  dashboard: {
    monthSpend: 'За месяц', yearSpend: 'За год', active: 'Активные', upcoming: 'Скоро', recent: 'Недавние',
    none: 'Нет данных', perMonth: '/мес', daysLeft: 'осталось {n} дн.', today: 'Сегодня',
    overdue: 'Просрочено', byCategory: 'По категориям', avgMonth: 'Ср. в месяц', expiringSoon: 'Скоро истекают', viewAll: 'Все',
    greeting: 'Привет, {name} 👋', subtitle: 'Обзор ваших подписок', catOverview: 'Все подписки по категориям'
  },
  sub: {
    add: 'Добавить', edit: 'Изменить', name: 'Название', amount: 'Сумма', currency: 'Валюта',
    category: 'Категория', payment: 'Оплата', billingType: 'Тип', recurring: 'Регулярная', oneTime: 'Разовая',
    cycle: 'Цикл', cycleCount: 'Каждые', day: 'день', week: 'неделя', month: 'месяц', year: 'год',
    startDate: 'Начало', nextRenewal: 'Продление', endDate: 'Конец', url: 'Ссылка', notes: 'Заметки',
    remindDays: 'Напомнить за (дней)', active: 'Активна', autoRenew: 'Автопродление',
    icon: 'Иконка', save: 'Сохранить', cancel: 'Отмена', delete: 'Удалить', renew: 'Продлить', confirmDelete: 'Удалить подписку?',
    uploadIcon: 'Загрузить иконку', filterAll: 'Все', filterRecurring: 'Регулярные', filterOneTime: 'Разовые',
    plan: 'Тариф', planPh: 'напр. Premium / Pro',
    secService: 'Сервис', secPrice: 'Цена', secBilling: 'Биллинг', secClassify: 'Категория и оплата',
    secFamily: 'Семейный доступ', secBundle: 'Пакет', secExtra: 'Доп.', secCalendar: 'Календарь',
    iconLibrary: 'Библиотека иконок', iconUrl: 'URL иконки', iconUrlImport: 'Импорт', nameSuggest: 'Популярные сервисы',
    family: 'Участники', familyAdd: 'Добавить', familyPh: 'Имя участника',
    bundleNone: 'Без пакета', bundleJoin: 'В существующий пакет', bundleCreate: 'Создать пакет', bundleName: 'Название пакета',
    showInCalendar: 'Показывать в календаре', website: 'Сайт',
    browse: 'По категориям', browseTitle: 'Выбор сервиса', searchPh: 'Поиск сервисов…', pickHint: 'Нажмите на сервис, чтобы заполнить название, иконку и сайт',
    secTrialCard: 'Пробный / Карта', trialEnd: 'Конец пробного', cancelBy: 'Отменить до', cardLast4: 'Карта (4 цифры)', cardExpiry: 'Срок карты (ММ/ГГ)',
    csvImported: 'Импортировано подписок: {n}', perMember: 'на чел.', trialTag: 'проб', cancelTag: 'отмена', cardTag: 'карта',
    renewTitle: 'Подтвердить продление', renewMsg: 'Выберите способ продления «{name}»:',
    renewToday: 'Поддержание / заранее: +1 цикл от сегодня (сброс цикла)',
    renewDue: 'Обычное: +1 цикл от текущей даты продления (без потери оплаченного)',
    renewNext: 'Следующее продление:', renewOk: 'Продлено, следующее {date}', confirm: 'Подтвердить',
    expiredTag: 'Истекло', soonTag: 'Скоро', uncategorized: 'Без категории', dragHint: 'Перетащите карточки для сортировки; заголовок категории — для порядка категорий',
    deleteTitle: 'Удалить подписку', deletePwdTip: 'Во избежание ошибок введите пароль, чтобы удалить «{name}»', pwdPh: 'Пароль',
    remark: 'Заметка', remarkPh: 'напр. основной сервер / HK CN2 (на карточке)',
    ipLabel: 'IP-адрес (необязательно)', ipv4: 'IPv4', ipv6: 'IPv6'
  },
  calendar: { title: 'Календарь продлений', noEvents: 'Нет продлений', today: 'Сегодня', more: '+{n} ещё' },
  reports: {
    title: 'Отчёты', overview: 'Обзор', insights: 'Аналитика', categoryDetail: 'По категориям', recentPayments: 'Платежи',
    ranking: 'Рейтинг', oneTime: 'Покупки', upcoming: 'Скоро', expired: 'Истёкшие',
    category: 'Категория', monthly: 'В месяц', percent: 'Доля', total: 'Итого в месяц', empty: 'Нет данных',
    exportCsv: 'Экспорт CSV', monthlyTotal: 'Итого в месяц', yearlyTotal: 'Итого в год', byCategory: 'Расходы по категориям', spendTrend: 'Обзор расходов',
    recurringSubs: 'Регулярные', permanentBuy: 'Покупки', count: 'Кол-во', amount: 'Сумма', date: 'Дата', type: 'Тип',
    permanentTotal: 'Сумма покупок', recurringMonthly: 'Регулярные в месяц', noData: 'Нет данных для графика'
  },
  settings: {
    title: 'Настройки', language: 'Язык', theme: 'Тема', baseCurrency: 'Базовая валюта', telegram: 'Telegram',
    tgEnabled: 'Включить уведомления Telegram', botToken: 'Bot Token', adminId: 'Admin ID',
    apiBase: 'Прокси TG API (опц.)', proxy: 'HTTP прокси (опц.)',
    chatId: 'Chat ID', botStatus: 'Статус бота', checkBot: 'Проверить', testSend: 'Тест',
    getUpdates: 'Получить Chat ID', save: 'Сохранить', saved: 'Сохранено', refreshRates: 'Обновить курсы', ratesUpdated: 'Курсы обновлены',
    themeLight: 'Светлая', themeDark: 'Тёмная', themeOcean: 'Океан', themeForest: 'Лес', themePurple: 'Фиолет',
    botOk: 'Бот в порядке', botFail: 'Ошибка', testOk: 'Тест отправлен', logs: 'Журнал',
    rateTable: 'Курсы валют', rateTip: 'Сегодняшняя стоимость 1 единицы в {base}', updatedAt: 'Обновлено', noRates: 'Нет данных, нажмите «Обновить курсы»'
  },
  backup: {
    title: 'Резервная копия',
    tip: 'Экспортируйте подписки и свои категории/способы оплаты в JSON. После переустановки импортируйте файл, чтобы восстановить данные.',
    export: 'Экспорт', import: 'Импорт', replace: 'Сначала очистить подписки',
    replaceConfirm: 'Все текущие подписки будут удалены перед импортом. Продолжить?',
    exportOk: 'Файл скачан', importOk: 'Импортировано подписок: {n}', importFail: 'Ошибка импорта: неверный файл'
  },
  backupAll: {
    title: 'Полная резервная копия сайта (админ)',
    tip: 'Экспортируйте аккаунты и данные всех участников в один JSON-файл. После переустановки импортируйте его, чтобы восстановить подписки, категории и т.д. всех пользователей.',
    export: 'Экспорт полной копии', import: 'Импорт полной копии', replace: 'Сначала очистить подписки каждого пользователя',
    importConfirm: 'Будут восстановлены данные всех участников из полной копии (отсутствующие аккаунты создаются заново). Продолжить?',
    replaceConfirm: 'Подписки каждого пользователя будут удалены перед импортом из полной копии. Продолжить?',
    exportOk: 'Полная копия скачана (пользователей: {n})', importOk: 'Восстановлено пользователей: {users} (создано: {created}), импортировано подписок: {n}'
  },
  cal: {
    title: 'Подписка на календарь', tip: 'Подпишитесь на даты продления в Apple / Google / Outlook Calendar с напоминаниями. Это ваша личная ссылка — не разглашайте.',
    get: 'Получить ссылку', copy: 'Копировать', reset: 'Сбросить', copied: 'Скопировано', resetOk: 'Ссылка сброшена (старая недействительна)'
  },
  autobk: {
    title: 'Локальное авто-резервирование', tip: 'Сервер каждую ночь экспортирует снимок всех данных в data/backups — дополнительная страховка.',
    run: 'Сделать резерв', keep: 'Хранит последние {n}', none: 'Файлов авто-бэкапа пока нет'
  },
  remind: {
    title: 'Напоминания и бюджет', budget: 'Месячный бюджет', budgetPh: '0 или пусто = без лимита',
    quietStart: 'Тихо с', quietEnd: 'Тихо до',
    quietHint: 'В тихие часы откладываются только несрочные напоминания; на сегодня/завтра — отправляются.',
    digest: 'Еженедельная сводка', over: 'Превышен бюджет', budgetLeft: 'Остаток бюджета'
  },
  wk: { mon: 'Пн', tue: 'Вт', wed: 'Ср', thu: 'Чт', fri: 'Пт', sat: 'Сб', sun: 'Вс' },
  sec: {
    title: 'Безопасность', twofa: 'Двухфакторная (2FA)', on: 'вкл', off: 'выкл', enable: 'Включить', disable: 'Выключить',
    confirmEnable: 'Подтвердить', scanTip: 'Отсканируйте в Google Authenticator / 1Password или введите ключ вручную:',
    enabledOk: '2FA включена', disabledOk: '2FA выключена', enterPwd: 'Введите пароль, чтобы выключить 2FA',
    apiTokens: 'API-токены', tokenName: 'Имя токена', tokenOnce: 'Скопируйте сейчас — показывается один раз:',
    neverUsed: 'не использован', revokeConfirm: 'Отозвать токен? Скрипты перестанут работать.'
  },
  upd: {
    title: 'Версия и обновления', check: 'Проверить обновления', newVersion: 'Доступна версия v{v}', isLatest: 'Установлена последняя версия', failed: 'Ошибка проверки (нет связи с GitHub)',
    howto: 'Как обновить (данные сохраняются, авто-миграция):', view: 'Что нового', banner: 'Доступна версия v{v} — см. Настройки',
    backupTip: 'Перед обновлением сделайте резервную копию.'
  },
  common: { loading: 'Загрузка...', save: 'Сохранить', actions: 'Действия', status: 'Статус', date: 'Дата', confirm: 'Подтвердить', cancel: 'Отмена', close: 'Закрыть' }
}

export default createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh',
  fallbackLocale: 'en',
  messages: { zh, en, ru }
})
