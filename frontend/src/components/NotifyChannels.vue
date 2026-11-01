<template>
  <div class="card sect notify">
    <p v-if="androidPreview" class="muted">{{ t('mobile.limited') }}</p>
    <p v-if="androidPreview && dirty" class="unsaved-note" role="status">{{ t('mobile.unsavedBadge') }}</p>
    <div class="secret-actions" v-if="androidPreview"><button type="button" class="btn ghost" :aria-pressed="showSecrets" @click="showSecrets = !showSecrets">{{ t(showSecrets ? 'mobile.hideSecrets' : 'mobile.showSecrets') }}</button></div>
    <div class="nc-head">
      <div class="nc-title">
        <h3><span class="hi" v-html="icon('notifyCfg')"></span>{{ t('notifyCfg.title') }}</h3>
        <p class="muted nc-sub">Telegram / 飞书 / QQ / Bark / Email / Pushplus / Webhook</p>
      </div>
      <button class="btn" :disabled="saving" @click="save"><span class="bi" v-html="icon('check')"></span>{{ t('notifyCfg.save') }}</button>
    </div>

    <div class="tiles" role="tablist">
      <button v-for="tb in tabs" :key="tb.key" type="button" role="tab" class="tile" :class="{ on: tab === tb.key }"
              :aria-selected="tab === tb.key" @click="tab = tb.key">
        <span class="tile-n">{{ tb.label }}</span>
        <span class="dot" :class="{ ok: cfg[tb.key] && cfg[tb.key].enabled }"></span>
      </button>
    </div>

    <div v-if="loaded" class="panel" role="tabpanel">
      <div class="ch-head">
        <h4>{{ enableLabel }}</h4>
        <div class="ch-actions">
          <button class="btn ghost sm" :disabled="testing || !!androidPreview" @click="test(tab)"><span class="bi" v-html="icon('send')"></span>{{ t('notifyCfg.test') }}</button>
          <label class="switch" :title="enableLabel"><input type="checkbox" v-model="cfg[tab].enabled" :aria-label="enableLabel" /><span class="track"></span></label>
        </div>
      </div>

      <!-- Telegram -->
      <div v-if="tab === 'telegram'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-telegram-bot_token`">BOT TOKEN</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-telegram-bot_token`" v-model="cfg.telegram.bot_token" placeholder="123456:ABC-..." /></div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-telegram-chat_id`">CHAT ID</label><input :id="`${fieldId}-cfg-telegram-chat_id`" v-model="cfg.telegram.chat_id" placeholder="-100xxxx / 数字" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-telegram-admin_id`">ADMIN ID</label><input :id="`${fieldId}-cfg-telegram-admin_id`" v-model="cfg.telegram.admin_id" /></div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-telegram-api_base`">{{ t('notifyCfg.tgApiBase') }}</label><input :id="`${fieldId}-cfg-telegram-api_base`" v-model="cfg.telegram.api_base" placeholder="api.telegram.org" /></div>
        <div class="f"><label :for="`${fieldId}-cfg-telegram-proxy`">{{ t('notifyCfg.httpProxy') }}</label><input :id="`${fieldId}-cfg-telegram-proxy`" v-model="cfg.telegram.proxy" placeholder="http://127.0.0.1:7890" /></div>
        <div class="row">
          <button class="btn ghost sm" :disabled="!!androidPreview" @click="tgAction('me')">{{ t('settings.checkBot') }}</button>
          <button class="btn ghost sm" :disabled="!!androidPreview" @click="tgAction('updates')">{{ t('settings.getUpdates') }}</button>
        </div>
      </div>

      <!-- 飞书 -->
      <div v-else-if="tab === 'feishu'" class="fields">
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-feishu-app_id`">APP ID</label><input :id="`${fieldId}-cfg-feishu-app_id`" v-model="cfg.feishu.app_id" placeholder="cli_xxxx" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-feishu-app_secret`">APP SECRET</label><input :type="androidPreview && showSecrets ? 'text' : 'password'" :id="`${fieldId}-cfg-feishu-app_secret`" v-model="cfg.feishu.app_secret" /></div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-feishu-chat_ids`">CHAT IDS</label><input :id="`${fieldId}-cfg-feishu-chat_ids`" v-model="cfg.feishu.chat_ids" placeholder="oc_xxxx，多个逗号分隔" />
          <small class="muted">{{ t('notifyCfg.feishuHint') }}</small></div>
      </div>

      <!-- QQ -->
      <div v-else-if="tab === 'qq'" class="fields">
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-qq-app_id`">APP ID</label><input :id="`${fieldId}-cfg-qq-app_id`" v-model="cfg.qq.app_id" placeholder="QQ Bot App ID" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-qq-app_secret`">APP SECRET</label><input :type="androidPreview && showSecrets ? 'text' : 'password'" :id="`${fieldId}-cfg-qq-app_secret`" v-model="cfg.qq.app_secret" /></div>
        </div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-qq-group_ids`">{{ t('notifyCfg.qqGroups') }}</label><input :id="`${fieldId}-cfg-qq-group_ids`" v-model="cfg.qq.group_ids" placeholder="群聊 OpenID，多个逗号分隔" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-qq-user_ids`">{{ t('notifyCfg.qqUsers') }}</label><input :id="`${fieldId}-cfg-qq-user_ids`" v-model="cfg.qq.user_ids" placeholder="用户 OpenID，多个逗号分隔" /></div>
        </div>
        <small class="muted">{{ t('notifyCfg.qqHint') }}</small>
      </div>

      <!-- Bark -->
      <div v-else-if="tab === 'bark'" class="fields">
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.targetUrls') }}</label>
            <button class="btn ghost sm" @click="cfg.bark.urls.push('')"><span class="bi" v-html="icon('plus')"></span>URL</button></div>
          <p v-if="!cfg.bark.urls.length" class="none">{{ t('notifyCfg.noBarkUrl') }}</p>
          <div v-for="(u, i) in cfg.bark.urls" :key="i" class="list-row">
            <input :aria-label="`${t('notifyCfg.targetUrls')} ${i + 1}`" v-model="cfg.bark.urls[i]" placeholder="https://api.day.app/你的Key" />
            <button class="x" aria-label="✕" @click="cfg.bark.urls.splice(i, 1)"><span v-html="icon('x')"></span></button>
          </div>
        </div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-bark-group`">{{ t('notifyCfg.barkGroup') }}</label><input :id="`${fieldId}-cfg-bark-group`" v-model="cfg.bark.group" placeholder="EasySub" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-bark-level`">{{ t('notifyCfg.barkLevel') }}</label>
            <select :id="`${fieldId}-cfg-bark-level`" v-model="cfg.bark.level">
              <option value="active">active</option><option value="timeSensitive">timeSensitive</option>
              <option value="passive">passive</option><option value="critical">critical</option>
            </select></div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-bark-icon`">ICON</label><input :id="`${fieldId}-cfg-bark-icon`" v-model="cfg.bark.icon" placeholder="图标 URL，可选" /></div>
      </div>

      <!-- Email -->
      <div v-else-if="tab === 'email'" class="fields">
        <div class="three">
          <div class="f"><label :for="`${fieldId}-cfg-email-host`">SMTP {{ t('notifyCfg.host') }}</label><input :id="`${fieldId}-cfg-email-host`" v-model="cfg.email.host" placeholder="smtp.example.com" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-email-port`">SMTP {{ t('notifyCfg.port') }}</label><input :id="`${fieldId}-cfg-email-port`" v-model.number="cfg.email.port" type="number" /></div>
          <div class="f sw"><label>SSL/TLS</label><label class="switch"><input type="checkbox" v-model="cfg.email.ssl" aria-label="SSL/TLS" /><span class="track"></span></label></div>
        </div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-email-username`">{{ t('notifyCfg.username') }}</label><input :id="`${fieldId}-cfg-email-username`" v-model="cfg.email.username" placeholder="邮箱账号" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-email-password`">{{ t('notifyCfg.password') }}</label><input :type="androidPreview && showSecrets ? 'text' : 'password'" :id="`${fieldId}-cfg-email-password`" v-model="cfg.email.password" placeholder="密码或授权码" /></div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-email-from`">{{ t('notifyCfg.from') }}</label><input :id="`${fieldId}-cfg-email-from`" v-model="cfg.email.from" placeholder="noreply@example.com" /></div>
        <div class="f"><label :for="`${fieldId}-cfg-email-to`">{{ t('notifyCfg.to') }}</label><input :id="`${fieldId}-cfg-email-to`" v-model="cfg.email.to" placeholder="多个收件人用英文逗号分隔" /></div>
      </div>

      <!-- Pushplus -->
      <div v-else-if="tab === 'pushplus'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-pushplus-token`">TOKEN</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-pushplus-token`" v-model="cfg.pushplus.token" placeholder="Pushplus 用户 Token" /></div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-pushplus-topic`">{{ t('notifyCfg.ppTopic') }}</label><input :id="`${fieldId}-cfg-pushplus-topic`" v-model="cfg.pushplus.topic" placeholder="群组编码，不填发给个人" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-pushplus-channel`">{{ t('notifyCfg.ppChannel') }}</label>
            <select :id="`${fieldId}-cfg-pushplus-channel`" v-model="cfg.pushplus.channel">
              <option value="wechat">微信 (wechat)</option><option value="mail">邮件 (mail)</option>
              <option value="webhook">Webhook</option><option value="cp">企业微信 (cp)</option>
            </select></div>
        </div>
      </div>

      <!-- Server酱 -->
      <div v-else-if="tab === 'serverchan'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-serverchan-sendkey`">SENDKEY</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-serverchan-sendkey`" v-model="cfg.serverchan.sendkey" placeholder="SCT... / SendKey" />
          <small class="muted">{{ t('notifyCfg.serverchanHint') }}</small></div>
      </div>

      <!-- 企业微信：群机器人 / 自建应用（对齐 CMSHelp「企业微信配置」） -->
      <div v-else-if="tab === 'wecom'" class="fields">
        <div class="f">
          <label>{{ t('notifyCfg.wecomMode') }}</label>
          <div class="seg wide">
            <button type="button" class="seg-b" :class="{ on: wecomMode === 'webhook' }" @click="cfg.wecom.mode = 'webhook'">
              {{ t('notifyCfg.wecomModeRobot') }}
            </button>
            <button type="button" class="seg-b" :class="{ on: wecomMode === 'app' }" @click="cfg.wecom.mode = 'app'">
              {{ t('notifyCfg.wecomModeApp') }}
            </button>
          </div>
          <small class="muted">{{ wecomMode === 'app' ? t('notifyCfg.wecomModeAppTip') : t('notifyCfg.wecomModeRobotTip') }}</small>
        </div>

        <!-- 群机器人 -->
        <template v-if="wecomMode === 'webhook'">
          <div class="f"><label :for="`${fieldId}-cfg-wecom-url`">{{ t('notifyCfg.robotUrl') }}</label>
            <input :id="`${fieldId}-cfg-wecom-url`" v-model="cfg.wecom.url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
            <small class="muted">{{ t('notifyCfg.wecomHint') }}</small></div>
        </template>

        <!-- 自建应用 -->
        <template v-else>
          <div class="f"><label :for="`${fieldId}-cfg-wecom-corp_id`">{{ t('notifyCfg.wecomCorpId') }}</label>
            <input :id="`${fieldId}-cfg-wecom-corp_id`" v-model="cfg.wecom.corp_id" placeholder="ww1234567890abcdef" />
            <small class="muted">{{ t('notifyCfg.wecomCorpIdHint') }}</small></div>
          <div class="two">
            <div class="f"><label :for="`${fieldId}-cfg-wecom-agent_id`">{{ t('notifyCfg.wecomAgentId') }}</label>
              <input :id="`${fieldId}-cfg-wecom-agent_id`" v-model="cfg.wecom.agent_id" placeholder="1000002" /></div>
            <div class="f"><label :for="`${fieldId}-cfg-wecom-secret`">{{ t('notifyCfg.wecomSecret') }}</label>
              <input :type="androidPreview && showSecrets ? 'text' : 'password'" :id="`${fieldId}-cfg-wecom-secret`" v-model="cfg.wecom.secret" placeholder="应用 Secret" /></div>
          </div>
          <small class="muted pull-up">{{ t('notifyCfg.wecomAgentHint') }}</small>
          <div class="f"><label :for="`${fieldId}-cfg-wecom-proxy_base`">{{ t('notifyCfg.wecomProxy') }}</label>
            <input :id="`${fieldId}-cfg-wecom-proxy_base`" v-model="cfg.wecom.proxy_base" placeholder="https://qyapi.weixin.qq.com（留空用官方域名）" />
            <small class="muted">{{ t('notifyCfg.wecomProxyHint') }}</small></div>
          <div class="three-e">
            <div class="f"><label :for="`${fieldId}-cfg-wecom-to_user`">{{ t('notifyCfg.wecomToUser') }}</label>
              <input :id="`${fieldId}-cfg-wecom-to_user`" v-model="cfg.wecom.to_user" placeholder="@all 或 UserID，多个用 | 分隔" /></div>
            <div class="f"><label :for="`${fieldId}-cfg-wecom-to_party`">{{ t('notifyCfg.wecomToParty') }}</label>
              <input :id="`${fieldId}-cfg-wecom-to_party`" v-model="cfg.wecom.to_party" placeholder="部门ID，可选" /></div>
            <div class="f"><label :for="`${fieldId}-cfg-wecom-to_tag`">{{ t('notifyCfg.wecomToTag') }}</label>
              <input :id="`${fieldId}-cfg-wecom-to_tag`" v-model="cfg.wecom.to_tag" placeholder="标签ID，可选" /></div>
          </div>
          <div class="two">
            <div class="f"><label :for="`${fieldId}-cfg-wecom-msg_type`">{{ t('notifyCfg.wecomMsgType') }}</label>
              <select :id="`${fieldId}-cfg-wecom-msg_type`" v-model="cfg.wecom.msg_type">
                <option value="text">{{ t('notifyCfg.wecomMsgText') }}</option>
                <option value="markdown">{{ t('notifyCfg.wecomMsgMd') }}</option>
                <option value="textcard">{{ t('notifyCfg.wecomMsgCard') }}</option>
              </select></div>
            <div class="f" v-if="cfg.wecom.msg_type === 'textcard'"><label :for="`${fieldId}-cfg-wecom-card_url`">{{ t('notifyCfg.wecomCardUrl') }}</label>
              <input :id="`${fieldId}-cfg-wecom-card_url`" v-model="cfg.wecom.card_url" placeholder="点击卡片跳转地址，如 http://你的域名/subs" /></div>
          </div>
          <div class="row">
            <button class="btn ghost sm" :disabled="checking || !!androidPreview" @click="wecomCheck">
              <span class="bi" v-html="icon('search')"></span>{{ t('notifyCfg.wecomCheck') }}
            </button>
          </div>
        </template>

        <!-- Web 端配置说明 -->
        <div class="help" :class="{ open: wecomHelp }">
          <button type="button" class="help-h" :aria-expanded="wecomHelp" @click="wecomHelp = !wecomHelp">
            <span class="help-t"><span class="hi sm" v-html="icon('library')"></span>{{ t('notifyCfg.wecomGuide') }}</span>
            <span class="chev" v-html="icon('chevron')"></span>
          </button>
          <div v-show="wecomHelp" class="help-b">
            <ol>
              <li v-for="(s, i) in (wecomMode === 'app' ? wecomSteps : wecomRobotSteps)" :key="i" v-html="s"></li>
            </ol>
            <template v-if="wecomMode === 'app'">
              <p class="warn"><span class="hi sm" v-html="icon('alert')"></span><span>{{ t('notifyCfg.wecomIpWarn') }}</span></p>
              <details>
                <summary><span class="chev" v-html="icon('chevron')"></span>{{ t('notifyCfg.wecomProxyExample') }}</summary>
                <pre>{{ nginxSnippet }}</pre>
                <p class="muted">{{ t('notifyCfg.wecomSocatTip') }}</p>
                <pre>{{ socatSnippet }}</pre>
              </details>
              <p class="muted">{{ t('notifyCfg.wecomAesTip') }}</p>
            </template>
            <p class="muted">{{ t('notifyCfg.wecomRef') }}
              <a href="https://github.com/guyue2005/CMSHelp/wiki/8.%E6%B6%88%E6%81%AF%E9%85%8D%E7%BD%AE" target="_blank" rel="noreferrer">CMSHelp Wiki · 消息配置</a>
            </p>
          </div>
        </div>
      </div>

      <!-- 钉钉 -->
      <div v-else-if="tab === 'dingtalk'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-dingtalk-url`">{{ t('notifyCfg.robotUrl') }}</label><input :id="`${fieldId}-cfg-dingtalk-url`" v-model="cfg.dingtalk.url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." /></div>
        <div class="f"><label :for="`${fieldId}-cfg-dingtalk-secret`">{{ t('notifyCfg.signSecret') }}</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-dingtalk-secret`" v-model="cfg.dingtalk.secret" placeholder="SEC... 加签密钥，选填" />
          <small class="muted">{{ t('notifyCfg.dingtalkHint') }}</small></div>
      </div>

      <!-- Discord -->
      <div v-else-if="tab === 'discord'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-discord-url`">Webhook URL</label><input :id="`${fieldId}-cfg-discord-url`" v-model="cfg.discord.url" placeholder="https://discord.com/api/webhooks/..." />
          <small class="muted">{{ t('notifyCfg.discordHint') }}</small></div>
      </div>

      <!-- Slack -->
      <div v-else-if="tab === 'slack'" class="fields">
        <div class="f"><label :for="`${fieldId}-cfg-slack-url`">Webhook URL</label><input :id="`${fieldId}-cfg-slack-url`" v-model="cfg.slack.url" placeholder="https://hooks.slack.com/services/..." />
          <small class="muted">{{ t('notifyCfg.slackHint') }}</small></div>
      </div>

      <!-- ntfy -->
      <div v-else-if="tab === 'ntfy'" class="fields">
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-ntfy-server`">{{ t('notifyCfg.server') }}</label><input :id="`${fieldId}-cfg-ntfy-server`" v-model="cfg.ntfy.server" placeholder="https://ntfy.sh" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-ntfy-topic`">Topic</label><input :id="`${fieldId}-cfg-ntfy-topic`" v-model="cfg.ntfy.topic" placeholder="your-topic" /></div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-ntfy-token`">{{ t('notifyCfg.tokenOptional') }}</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-ntfy-token`" v-model="cfg.ntfy.token" placeholder="tk_... 访问令牌，选填" />
          <small class="muted">{{ t('notifyCfg.ntfyHint') }}</small></div>
      </div>

      <!-- Gotify -->
      <div v-else-if="tab === 'gotify'" class="fields">
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-gotify-server`">{{ t('notifyCfg.server') }}</label><input :id="`${fieldId}-cfg-gotify-server`" v-model="cfg.gotify.server" placeholder="https://gotify.example.com" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-gotify-token`">App Token</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-gotify-token`" v-model="cfg.gotify.token" placeholder="应用 Token" /></div>
        </div>
        <div class="f narrow"><label :for="`${fieldId}-cfg-gotify-priority`">{{ t('notifyCfg.priority') }}</label><input :id="`${fieldId}-cfg-gotify-priority`" v-model.number="cfg.gotify.priority" type="number" /></div>
      </div>

      <!-- Webhook -->
      <div v-else-if="tab === 'webhook'" class="fields">
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.targetUrls') }}</label>
            <button class="btn ghost sm" @click="cfg.webhook.urls.push('')"><span class="bi" v-html="icon('plus')"></span>URL</button></div>
          <p v-if="!cfg.webhook.urls.length" class="none">{{ t('notifyCfg.noWebhookUrl') }}</p>
          <div v-for="(u, i) in cfg.webhook.urls" :key="i" class="list-row">
            <input :aria-label="`${t('notifyCfg.targetUrls')} ${i + 1}`" v-model="cfg.webhook.urls[i]" placeholder="https://example.com/hook" />
            <button class="x" aria-label="✕" @click="cfg.webhook.urls.splice(i, 1)"><span v-html="icon('x')"></span></button>
          </div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-webhook-secret`">{{ t('notifyCfg.whSecret') }}</label><input :type="androidPreview && !showSecrets ? 'password' : 'text'" :id="`${fieldId}-cfg-webhook-secret`" v-model="cfg.webhook.secret" placeholder="HMAC-SHA256 签名密钥，选填" />
          <small class="muted">{{ t('notifyCfg.whSecretHint') }}</small></div>
        <div class="f">
          <div class="f-h"><label>{{ t('notifyCfg.whHeaders') }}</label>
            <button class="btn ghost sm" @click="cfg.webhook.headers.push({ key: '', value: '' })"><span class="bi" v-html="icon('plus')"></span>Header</button></div>
          <div v-for="(h, i) in cfg.webhook.headers" :key="i" class="list-row hdr">
            <input :aria-label="`${t('notifyCfg.whHeaders')} ${i + 1} key`" v-model="h.key" placeholder="Authorization" class="hk" />
            <input :type="androidPreview && !showSecrets ? 'password' : 'text'" :aria-label="`${t('notifyCfg.whHeaders')} ${i + 1} value`" v-model="h.value" placeholder="值" class="hv" />
            <button class="x" aria-label="✕" @click="cfg.webhook.headers.splice(i, 1)"><span v-html="icon('x')"></span></button>
          </div>
        </div>
        <div class="f"><label :for="`${fieldId}-cfg-webhook-template`">{{ t('notifyCfg.whTemplate') }}</label>
          <textarea :id="`${fieldId}-cfg-webhook-template`" v-model="cfg.webhook.template" rows="2" class="mono" :placeholder="tplPlaceholder"></textarea>
          <small class="muted">{{ t('notifyCfg.whTemplateHint') }}</small></div>
        <div class="two">
          <div class="f"><label :for="`${fieldId}-cfg-webhook-timeout_ms`">{{ t('notifyCfg.whTimeout') }}</label><input :id="`${fieldId}-cfg-webhook-timeout_ms`" v-model.number="cfg.webhook.timeout_ms" type="number" /></div>
          <div class="f"><label :for="`${fieldId}-cfg-webhook-max_retries`">{{ t('notifyCfg.whRetries') }}</label><input :id="`${fieldId}-cfg-webhook-max_retries`" v-model.number="cfg.webhook.max_retries" type="number" /></div>
        </div>
      </div>

      <p v-if="msg" class="msg" :class="ok ? 'ok' : 'err'" role="status">
        <span class="mi" v-html="icon(ok ? 'check' : 'alert')"></span><span>{{ msg }}</span>
      </p>
    </div>
    <p v-else class="muted">{{ t('common.loading') }}</p>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, useId } from 'vue'
import { useUnsavedChanges } from '../android-preview/useUnsavedChanges.js'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { icon } from '../icons'

const { t } = useI18n()
const tab = ref('telegram')
const loaded = ref(false)
const saving = ref(false)
const testing = ref(false)
const msg = ref('')
const ok = ref(false)
const cfg = ref(defaults())
const androidPreview = inject('preview', null)
const showSecrets = ref(false)
const fieldId = useId()
const savedConfig = ref('')
const dirty = computed(() => loaded.value && JSON.stringify(cfg.value) !== savedConfig.value)
useUnsavedChanges(() => !!androidPreview && dirty.value, () => t('mobile.unsaved'))
const tplPlaceholder = '{{subject}} {{text}}'
const checking = ref(false)
const wecomHelp = ref(false)
const wecomMode = computed(() => cfg.value.wecom?.mode || 'webhook')
// 说明文案含 <b> 标记，来自 i18n 静态词条（非用户输入），故用 v-html 渲染
const wecomSteps = computed(() => [1, 2, 3, 4, 5, 6].map((i) => t(`notifyCfg.wecomStep${i}`)))
const wecomRobotSteps = computed(() => [1, 2, 3].map((i) => t(`notifyCfg.wecomRStep${i}`)))
const nginxSnippet = `location ^~ /cgi-bin/gettoken       { proxy_pass https://qyapi.weixin.qq.com; }
location ^~ /cgi-bin/message/send   { proxy_pass https://qyapi.weixin.qq.com; }
location ^~ /cgi-bin/agent/get      { proxy_pass https://qyapi.weixin.qq.com; }`
const socatSnippet = `services:
  wxproxy:
    image: alpine/socat
    command: TCP-LISTEN:9090,fork,reuseaddr TCP:qyapi.weixin.qq.com:443
    ports: ["8543:9090"]
    restart: always`

const tabs = [
  { key: 'telegram', label: 'Telegram Bot' }, { key: 'feishu', label: '飞书 Bot' },
  { key: 'qq', label: 'QQ Bot' }, { key: 'bark', label: 'Bark' }, { key: 'email', label: 'Email' },
  { key: 'pushplus', label: 'Pushplus' }, { key: 'serverchan', label: 'Server酱' },
  { key: 'wecom', label: '企业微信' }, { key: 'dingtalk', label: '钉钉' },
  { key: 'discord', label: 'Discord' }, { key: 'slack', label: 'Slack' },
  { key: 'ntfy', label: 'ntfy' }, { key: 'gotify', label: 'Gotify' },
  { key: 'webhook', label: 'Webhook' }
]
const enableLabels = {
  telegram: '启用 Telegram 机器人', feishu: '启用飞书机器人', qq: '启用 QQ 机器人',
  bark: '启用 Bark 推送', email: '启用 Email 推送', pushplus: '启用 Pushplus 推送',
  serverchan: '启用 Server酱', wecom: '启用企业微信通知', dingtalk: '启用钉钉机器人',
  discord: '启用 Discord', slack: '启用 Slack', ntfy: '启用 ntfy', gotify: '启用 Gotify',
  webhook: '启用 Webhook 推送'
}
const enableLabel = computed(() => enableLabels[tab.value])

// 客户端默认结构：与后端保持一致，防止某渠道/字段缺失导致模板访问 undefined（webhook 空白根因防御）
function defaults() {
  return {
    telegram: { enabled: false, bot_token: '', chat_id: '', admin_id: '', api_base: '', proxy: '' },
    feishu: { enabled: false, app_id: '', app_secret: '', chat_ids: '' },
    qq: { enabled: false, app_id: '', app_secret: '', group_ids: '', user_ids: '' },
    bark: { enabled: false, urls: [], group: '', level: 'active', icon: '' },
    email: { enabled: false, host: '', port: 465, ssl: true, username: '', password: '', from: '', to: '' },
    pushplus: { enabled: false, token: '', topic: '', channel: 'wechat' },
    serverchan: { enabled: false, sendkey: '' },
    wecom: {
      enabled: false, mode: 'webhook', url: '',
      corp_id: '', agent_id: '', secret: '', proxy_base: '',
      to_user: '@all', to_party: '', to_tag: '', msg_type: 'text', card_url: ''
    },
    dingtalk: { enabled: false, url: '', secret: '' },
    discord: { enabled: false, url: '' },
    slack: { enabled: false, url: '' },
    ntfy: { enabled: false, server: 'https://ntfy.sh', topic: '', token: '' },
    gotify: { enabled: false, server: '', token: '', priority: 5 },
    webhook: { enabled: false, urls: [], secret: '', headers: [], template: '', timeout_ms: 5000, max_retries: 3 }
  }
}

function flash(good, text) { ok.value = good; msg.value = text; setTimeout(() => (msg.value = ''), 4000) }

async function load() {
  const base = defaults()
  try {
    const { data } = await api.get('/api/notifications/config')
    const got = data.config || {}
    for (const k of Object.keys(base)) {
      if (got[k] && typeof got[k] === 'object') Object.assign(base[k], got[k])
      // 数组字段确保是数组，避免 v-for over null
      if (!Array.isArray(base[k].urls) && 'urls' in base[k]) base[k].urls = []
      if (k === 'webhook' && !Array.isArray(base[k].headers)) base[k].headers = []
    }
  } catch { /* 用默认值 */ }
  cfg.value = base
  savedConfig.value = JSON.stringify(base)
  loaded.value = true
}

async function save() {
  saving.value = true
  try {
    await api.put('/api/notifications/config', { config: cfg.value })
    savedConfig.value = JSON.stringify(cfg.value)
    flash(true, t('notifyCfg.saved'))
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') } finally { saving.value = false }
}

async function test(channel) {
  testing.value = true; msg.value = ''
  try {
    await api.post('/api/notifications/test', { channel, config: cfg.value[channel] })
    flash(true, t('notifyCfg.testOk'))
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') } finally { testing.value = false }
}

async function wecomCheck() {
  checking.value = true; msg.value = ''
  try {
    const { data } = await api.post('/api/notifications/wecom/check', { config: cfg.value.wecom })
    const a = data.agent || {}
    flash(true, `${t('notifyCfg.wecomCheckOk')}「${a.name}」· AgentId ${a.agentid} · ${t('notifyCfg.wecomScope')}: ${a.users} / ${a.parties} / ${a.tags}`)
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') } finally { checking.value = false }
}

async function tgAction(kind) {
  msg.value = ''
  try {
    await api.put('/api/notifications/config', { config: cfg.value })
    savedConfig.value = JSON.stringify(cfg.value)
    if (kind === 'me') {
      const { data } = await api.get('/api/notifications/telegram/me')
      flash(true, `${t('settings.botOk')}: @${data.result?.username}`)
    } else {
      const { data } = await api.get('/api/notifications/telegram/updates')
      const ids = (data.result || []).map((u) => u.message?.chat?.id).filter(Boolean)
      if (ids.length) { cfg.value.telegram.chat_id = String(ids[ids.length - 1]); flash(true, 'Chat IDs: ' + [...new Set(ids)].join(', ')) }
      else flash(false, 'No messages yet')
    }
  } catch (e) { flash(false, e.response?.data?.detail || 'Error') }
}

onMounted(load)
</script>

<style scoped>
/* ---------- 头部 ---------- */
.nc-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.nc-title { min-width: 0; }
.notify h3 { display: flex; align-items: center; gap: 9px; margin: 0; }
.nc-sub { font-size: 13px; margin: 4px 0 0; overflow-wrap: anywhere; }
.hi { display: inline-flex; width: 18px; height: 18px; flex-shrink: 0; color: var(--text-soft); }
.hi.sm { width: 15px; height: 15px; }
.bi { display: inline-flex; }

/* ---------- 渠道磁贴 ---------- */
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(124px, 1fr)); gap: 6px; margin-bottom: 14px; }
.tile { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 40px;
  padding: 0 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface);
  color: var(--text-soft); font: inherit; font-size: 13px; font-weight: 550; text-align: left; cursor: pointer;
  transition: border-color .15s, background-color .15s, color .15s; }
.tile:hover { border-color: var(--border-strong); color: var(--text); }
.tile.on { border-color: var(--primary); background: var(--primary-soft); color: var(--text);
  box-shadow: inset 0 0 0 1px var(--primary); }
.tile:focus-visible { outline: none; box-shadow: var(--focus); }
.tile-n { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tile .dot { width: 7px; height: 7px; }

/* ---------- 子面板（非嵌套卡片） ---------- */
.panel { padding: 18px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface-2); }
.ch-head { display: flex; justify-content: space-between; align-items: center; gap: 10px 14px; flex-wrap: wrap;
  padding-bottom: 14px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.ch-head h4 { margin: 0; font-size: 15px; font-weight: 650; }
.ch-actions { display: flex; align-items: center; gap: 12px; }

/* ---------- 字段 ---------- */
.fields { display: flex; flex-direction: column; gap: 14px; }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.three { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; gap: 14px; align-items: end; }
.three-e { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.f { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.f.sw { align-items: flex-start; }
.f.narrow { max-width: 160px; }
.f label { margin: 0; font-size: 13px; font-weight: 500; color: var(--text-soft); }
.f-h { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.f small, .fields > small { font-size: 12.5px; line-height: 1.55; overflow-wrap: anywhere; }
.pull-up { margin-top: -6px; }
.mono { font-family: var(--mono); font-size: 13px; }
.none { margin: 0; padding: 12px; border: 1px dashed var(--border-strong); border-radius: var(--radius-sm);
  text-align: center; color: var(--text-soft); font-size: 13px; }
.list-row { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.list-row input { flex: 1; min-width: 0; }
.list-row.hdr .hk { flex: 1; }
.list-row.hdr .hv { flex: 1.4; }
.x { display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; width: 40px; height: 40px;
  padding: 0; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface);
  color: var(--text-soft); cursor: pointer; transition: color .15s, border-color .15s, background-color .15s; }
.x span { display: inline-flex; width: 16px; height: 16px; }
.x:hover { color: var(--late); border-color: color-mix(in srgb, var(--late) 35%, var(--border)); background: var(--late-soft); }
.row { display: flex; flex-wrap: wrap; gap: 8px; }

/* ---------- 开关（复选框保留在 DOM 中，可聚焦） ---------- */
.switch { position: relative; display: inline-flex; align-items: center; margin: 0; min-height: 40px; cursor: pointer; }
.switch input { position: absolute; inset: 0; width: 100%; height: 100%; min-height: 0; margin: 0; opacity: 0; cursor: pointer; }
.switch .track { position: relative; width: 36px; height: 22px; border-radius: 999px; background: var(--border-strong);
  transition: background-color .2s var(--ease-out); pointer-events: none; }
.switch .track::after { content: ''; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%;
  background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: transform .22s var(--ease-out); }
.switch input:checked + .track { background: var(--primary); }
.switch input:checked + .track::after { transform: translateX(14px); background: var(--on-primary); }
.switch input:focus-visible + .track { box-shadow: var(--focus); }

/* ---------- 状态 ---------- */
.msg { display: flex; align-items: flex-start; gap: 6px; margin: 14px 0 0; font-size: 13px; line-height: 1.5; overflow-wrap: anywhere; }
.msg.ok { color: var(--ok); }
.msg.err { color: var(--late); }
.mi { display: inline-flex; width: 15px; height: 15px; flex-shrink: 0; margin-top: 2px; }

/* ---------- 企业微信：模式切换 ---------- */
.seg.wide { display: flex; width: 100%; }
.seg.wide .seg-b { flex: 1; min-height: 36px; white-space: normal; line-height: 1.3; }

/* ---------- 配置说明（安静的折叠区） ---------- */
.help { border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); }
.help-h { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px; min-height: 42px;
  border: none; background: transparent; padding: 0 14px; cursor: pointer; font: inherit; font-size: 13px;
  font-weight: 550; color: var(--text-soft); text-align: left; border-radius: var(--radius-sm); }
.help-h:hover { color: var(--text); }
.help-t { display: inline-flex; align-items: center; gap: 8px; }
.chev { display: inline-flex; width: 15px; height: 15px; flex-shrink: 0; color: var(--text-faint);
  transition: transform .2s var(--ease-out); }
.help.open > .help-h .chev { transform: rotate(90deg); }
.help-b { padding: 2px 14px 14px; font-size: 13px; line-height: 1.75; color: var(--text-soft); overflow-wrap: anywhere; }
.help-b ol { margin: 0 0 10px; padding-left: 20px; }
.help-b li { margin-bottom: 4px; }
.help-b :deep(b) { color: var(--text); font-weight: 600; }
.help-b .warn { display: flex; align-items: flex-start; gap: 8px; margin: 0 0 10px; padding: 9px 11px;
  border-radius: var(--radius-xs); background: var(--soon-soft); color: var(--text); }
.help-b .warn .hi { color: var(--soon); margin-top: 4px; }
.help-b details { margin: 0 0 8px; }
.help-b summary { display: inline-flex; align-items: center; gap: 6px; min-height: 32px; cursor: pointer;
  color: var(--text); font-weight: 550; user-select: none; list-style: none; }
.help-b summary::-webkit-details-marker { display: none; }
.help-b details[open] > summary .chev { transform: rotate(90deg); }
.help-b pre { margin: 8px 0; padding: 10px 12px; border-radius: var(--radius-xs); background: var(--surface-2);
  border: 1px solid var(--border); overflow-x: auto; font-size: 12px; line-height: 1.6; color: var(--text);
  white-space: pre; font-family: var(--mono); max-width: 100%; }
.help-b p { margin: 6px 0 0; }

@media (max-width: 720px) {
  .nc-head > .btn { width: 100%; }
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .panel { padding: 14px; }
  .two, .three, .three-e { grid-template-columns: minmax(0, 1fr); }
  .f.narrow { max-width: none; }
  .btn.sm { min-height: 40px; }
  .ch-actions { width: 100%; justify-content: space-between; }
  .list-row.hdr { flex-wrap: wrap; }
  .list-row.hdr .hk, .list-row.hdr .hv { flex: 1 1 40%; }
}
</style>
