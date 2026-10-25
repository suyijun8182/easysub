<template>
  <div class="subs">
    <header class="page-head">
      <div>
        <h1>{{ t('nav.subscriptions') }}</h1>
        <p class="lede">
          <span v-if="lateN" class="lede-late">{{ t('dashboard.summaryLate', { n: lateN }) }}</span>
          <span v-if="soonN" class="lede-soon">{{ t('dashboard.summarySoon', { n: soonN }) }}</span>
          <span v-if="!lateN && !soonN && subs.length" class="lede-ok">{{ t('dashboard.summaryClear') }}</span>
        </p>
      </div>
      <button class="btn" @click="openNew"><span class="i" v-html="icon('plus')"></span>{{ t('sub.add') }}</button>
    </header>

    <div class="toolbar">
      <div class="seg">
        <button :class="{ on: filter === '' }" :aria-pressed="filter === ''" @click="setFilter('')">{{ t('sub.filterAll') }}</button>
        <button :class="{ on: filter === 'recurring' }" :aria-pressed="filter === 'recurring'" @click="setFilter('recurring')">{{ t('sub.filterRecurring') }}</button>
        <button :class="{ on: filter === 'one_time' }" :aria-pressed="filter === 'one_time'" @click="setFilter('one_time')">{{ t('sub.filterOneTime') }}</button>
      </div>
      <label class="search">
        <span class="i" v-html="icon('search')"></span>
        <input v-model="search" type="search" :placeholder="t('sub.searchPh')" :aria-label="t('sub.searchPh')" />
      </label>
      <div class="tb-right">
        <button class="btn ghost sm" :class="{ on: manage === 'sort' }" :aria-pressed="manage === 'sort'"
                :disabled="!subs.length" @click="setManage('sort')">
          <span class="i" v-html="icon('grip')"></span>{{ t('sub.sortMode') }}</button>
        <button class="btn ghost sm" :class="{ on: manage === 'select' }" :aria-pressed="manage === 'select'"
                :disabled="!subs.length" @click="setManage('select')">
          <span class="i" v-html="icon('check')"></span>{{ t('sub.selectMode') }}</button>
        <button class="btn ghost sm" @click="exportCsv"><span class="i" v-html="icon('download')"></span>CSV</button>
        <label class="btn ghost sm"><span class="i" v-html="icon('upload')"></span>CSV
          <input type="file" accept=".csv,text/csv" hidden @change="importCsv" />
        </label>
      </div>
    </div>
    <p v-if="manage === 'sort'" class="drag-hint mode-hint muted" role="status">
      <span class="i" v-html="icon('grip')"></span>{{ t('sub.sortHint') }}</p>
    <p v-else class="drag-hint muted"><span class="i" v-html="icon('grip')"></span>{{ t('sub.dragHint') }}</p>

    <div v-if="!subs.length" class="card empty">
      <span v-html="icon('subscriptions')"></span>
      <b>{{ t('dashboard.none') }}</b>
      <button class="btn" style="margin-top:12px" @click="openNew"><span class="i" v-html="icon('plus')"></span>{{ t('sub.add') }}</button>
    </div>

    <!-- 按分类分组 -->
    <section v-for="(g, gi) in grouped" :key="g.key" class="cat-group"
         :class="{ 'drop-cat': dragOverCat === g.key }"
         :draggable="!manage"
         @dragstart="onCatDragStart(g.key, $event)"
         @dragover.prevent="onCatDragOver(g.key)"
         @dragend="clearDrag"
         @drop="onCatDrop(g.key)">
      <div class="cat-head">
        <span class="grip" v-html="icon('grip')"></span>
        <span class="cat-ico" v-if="g.icon">{{ g.icon }}</span>
        <h2 class="cat-name">{{ g.name }}</h2>
        <span class="tag num">{{ g.items.length }}</span>
        <span class="cat-line"></span>
        <!-- 排序模式：分类上移 / 下移（未分类固定在最后，不参与排序） -->
        <template v-if="manage === 'sort' && g.key !== NONE">
          <button class="btn sm ghost icon" :disabled="gi === 0"
                  :aria-label="t('sub.moveCatUp', { name: g.name })" :title="t('sub.moveCatUp', { name: g.name })"
                  @click="moveCat(g.key, -1)"><span class="i" v-html="icon('chevronU')"></span></button>
          <button class="btn sm ghost icon" :disabled="!canMoveCatDown(g.key)"
                  :aria-label="t('sub.moveCatDown', { name: g.name })" :title="t('sub.moveCatDown', { name: g.name })"
                  @click="moveCat(g.key, 1)"><span class="i" v-html="icon('chevronD')"></span></button>
        </template>
        <button v-if="manage === 'select'" class="btn sm ghost" @click="toggleGroup(g)">
          {{ g.items.every((s) => selected.has(s.id)) ? t('sub.selectNone') : t('sub.selectAll') }}</button>
      </div>

      <div class="sub-grid">
        <article v-for="(s, i) in g.items" :key="s.id" class="sub-card"
             :class="['is-' + statusOf(s), { inactive: !s.is_active, 'drop-card': dragOverSub === s.id,
                      picked: manage === 'select' && selected.has(s.id) }]"
             :draggable="!manage"
             @dragstart.stop="onCardDragStart(g.key, s.id, $event)"
             @dragover.prevent.stop="onCardDragOver(g.key, s.id)"
             @dragend="clearDrag"
             @drop.stop="onCardDrop(g.key, s.id)">
          <div class="sc-head">
            <input v-if="manage === 'select'" type="checkbox" class="sc-check" :checked="selected.has(s.id)"
                   :aria-label="t('sub.selectOne', { name: s.name })" @change="toggleSel(s.id)" />
            <SubIcon :icon="s.icon" :name="s.name" :size="44" />
            <div class="sc-title">
              <div class="sc-name" :title="s.name">{{ s.name }}</div>
              <div class="sc-plan muted" v-if="s.plan">{{ s.plan }}</div>
            </div>
            <span v-if="statusOf(s) === 'late'" class="tag late"><span class="i" v-html="icon('alert')"></span>{{ t('sub.expiredTag') }}</span>
            <span v-else-if="statusOf(s) === 'soon'" class="tag soon"><span class="i" v-html="icon('clock')"></span>{{ t('sub.soonTag') }}</span>
            <span v-else-if="s.billing_type === 'one_time'" class="tag">{{ t('sub.oneTime') }}</span>
          </div>

          <p v-if="s.remark" class="sc-remark">{{ s.remark }}</p>

          <div class="sc-money">
            <span class="amt num">{{ s.amount.toFixed(2) }}</span>
            <span class="cur">{{ s.currency }}</span>
            <span v-if="s.billing_type === 'recurring'" class="cycle">/ {{ cycleText(s) }}</span>
          </div>

          <div v-if="s.billing_type === 'recurring' && s.next_renewal_date" class="sc-count">
            <div class="sc-count-t">
              <span class="left" :class="statusOf(s)">{{ dueText(s) }}</span>
              <span class="date num muted">{{ t('sub.nextRenewal') }} {{ s.next_renewal_date }}</span>
            </div>
            <div v-bind="lifeAttrs(s, i)"><i :style="lifeBar(s).fill"></i></div>
          </div>

          <dl class="sc-facts">
            <div v-if="s.ipv4"><dt>IPv4</dt><dd class="mono">{{ s.ipv4 }}</dd></div>
            <div v-if="s.ipv6"><dt>IPv6</dt><dd class="mono">{{ s.ipv6 }}</dd></div>
            <div v-if="payName(s)"><dt>{{ t('sub.payment') }}</dt><dd>{{ payName(s) }}</dd></div>
            <div v-if="s.billing_type === 'recurring'"><dt>{{ t('sub.autoRenew') }}</dt>
              <dd><span class="i yn" :class="{ on: s.auto_renew }" v-html="icon(s.auto_renew ? 'check' : 'x')"></span></dd></div>
            <div v-if="s.family_members && s.family_members.length"><dt>{{ t('sub.family') }}</dt><dd>{{ s.family_members.join('、') }}</dd></div>
          </dl>

          <div v-if="manage === 'sort'" class="sc-acts">
            <button class="btn sm ghost" :disabled="i === 0" :aria-label="t('sub.moveUp') + ' · ' + s.name"
                    @click="moveSub(g.key, s.id, -1)"><span class="i" v-html="icon('chevronU')"></span>{{ t('sub.moveUp') }}</button>
            <button class="btn sm ghost" :disabled="i === g.items.length - 1" :aria-label="t('sub.moveDown') + ' · ' + s.name"
                    @click="moveSub(g.key, s.id, 1)"><span class="i" v-html="icon('chevronD')"></span>{{ t('sub.moveDown') }}</button>
          </div>
          <div v-else-if="manage !== 'select'" class="sc-acts">
            <button v-if="s.billing_type === 'recurring'" class="btn sm renew" @click="askRenew(s)">
              <span class="i" v-html="icon('renew')"></span>{{ t('sub.renew') }}</button>
            <button class="btn sm ghost" @click="openEdit(s)"><span class="i" v-html="icon('edit')"></span>{{ t('sub.edit') }}</button>
            <button class="btn sm ghost danger icon" :aria-label="t('sub.delete')" :title="t('sub.delete')" @click="askDelete(s)">
              <span class="i" v-html="icon('trash')"></span></button>
          </div>
        </article>
      </div>
    </section>

    <!-- 多选模式：批量操作条 -->
    <div v-if="manage === 'select'" class="bulk-bar" role="toolbar" :aria-label="t('sub.selectMode')">
      <span class="bulk-n num" role="status">{{ t('sub.selectedN', { n: selected.size }) }}</span>
      <button class="btn sm ghost" @click="toggleAllVisible">
        {{ allVisibleSelected ? t('sub.selectNone') : t('sub.selectAll') }}</button>
      <span class="bulk-sep"></span>
      <button class="btn sm" :disabled="!selectedRecurring.length || bulkBusy" @click="askBulkRenew">
        <span class="i" v-html="icon('renew')"></span>{{ t('sub.renew') }}</button>
      <button class="btn sm ghost" :disabled="!selected.size || bulkBusy" @click="bulkSetActive(true)">{{ t('sub.enable') }}</button>
      <button class="btn sm ghost" :disabled="!selected.size || bulkBusy" @click="bulkSetActive(false)">{{ t('sub.disable') }}</button>
      <select class="bulk-cat" :disabled="!selected.size || bulkBusy" :aria-label="t('sub.moveToCat')"
              :value="''" @change="bulkSetCategory($event)">
        <option value="" disabled>{{ t('sub.moveToCat') }}</option>
        <option value="none">— {{ t('sub.uncategorized') }}</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
      </select>
      <button class="btn sm ghost danger" :disabled="!selected.size || bulkBusy" @click="askBulkDelete">
        <span class="i" v-html="icon('trash')"></span>{{ t('sub.delete') }}</button>
      <button class="btn sm ghost bulk-done" @click="setManage('select')">{{ t('sub.done') }}</button>
    </div>

    <!-- 续费确认弹窗（单个 / 批量） -->
    <BaseModal v-if="renewTarget || renewBulk" style="width:460px" @close="closeRenew" v-slot="{ titleId }">
        <h3 :id="titleId">{{ t('sub.renewTitle') }}</h3>
        <p style="font-size:14px;line-height:1.6">{{ renewBulk
          ? t('sub.bulkRenewMsg', { n: selectedRecurring.length })
          : t('sub.renewMsg', { name: renewTarget.name }) }}</p>
        <label class="opt" :class="{ on: renewMode === 'today' }">
          <input type="radio" value="today" v-model="renewMode" />
          <div>
            <div>{{ t('sub.renewToday') }}</div>
            <div v-if="!renewBulk" class="muted opt-d num">{{ t('sub.nextRenewal') }}：{{ previewToday }}</div>
          </div>
        </label>
        <label class="opt" :class="{ on: renewMode === 'due' }">
          <input type="radio" value="due" v-model="renewMode" />
          <div>
            <div>{{ t('sub.renewDue') }}</div>
            <div v-if="!renewBulk" class="muted opt-d num">{{ t('sub.nextRenewal') }}：{{ previewDue }}</div>
          </div>
        </label>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="closeRenew">{{ t('sub.cancel') }}</button>
          <button class="btn" :disabled="renewing" @click="confirmRenew">{{ t('sub.confirm') }}</button>
        </div>
    </BaseModal>

    <!-- 删除确认（需验证密码；单个 / 批量） -->
    <BaseModal v-if="delTarget || delBulk" style="width:420px" @close="closeDelete" v-slot="{ titleId }">
        <h3 :id="titleId">{{ t('sub.deleteTitle') }}</h3>
        <p id="del-tip" style="font-size:14px;line-height:1.6">{{ delBulk
          ? t('sub.bulkDeleteTip', { n: selected.size })
          : t('sub.deletePwdTip', { name: delTarget.name }) }}</p>
        <input v-model="delPwd" type="password" autocomplete="current-password" :aria-label="t('sub.pwdPh')"
               aria-describedby="del-tip" :placeholder="t('sub.pwdPh')" @keyup.enter="confirmDelete" />
        <p v-if="delErr" class="err" role="alert">{{ delErr }}</p>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="closeDelete">{{ t('sub.cancel') }}</button>
          <button class="btn danger" :disabled="deleting || !delPwd" @click="confirmDelete">{{ t('sub.delete') }}</button>
        </div>
    </BaseModal>

    <!-- 添加/编辑订阅 -->
    <BaseModal v-if="showForm" @close="showForm = false" v-slot="{ titleId }">
        <h3 :id="titleId">{{ form.id ? t('sub.edit') : t('sub.add') }}</h3>

        <div class="block">
          <div class="block-t">{{ t('sub.secService') }}</div>
          <div class="row">
            <div class="icon-pick">
              <SubIcon :icon="form.icon" :name="form.name" :size="40" />
            </div>
            <div style="flex:2;position:relative">
              <label for="sf-name">{{ t('sub.name') }}</label>
              <input id="sf-name" v-model="form.name" @input="onNameInput" @keydown.esc="closeSuggest" autocomplete="off" />
              <div v-if="suggestions.length" class="suggest">
                <button v-for="s in suggestions" :key="s.slug" type="button" class="suggest-i" @click="pickService(s)">
                  <img :src="s.icon" alt="" class="ico" /> {{ s.name }}
                </button>
              </div>
            </div>
            <div style="flex:1">
              <label for="sf-plan">{{ t('sub.plan') }}</label>
              <input id="sf-plan" v-model="form.plan" :placeholder="t('sub.planPh')" />
            </div>
          </div>
          <label for="sf-remark">{{ t('sub.remark') }}</label>
          <input id="sf-remark" v-model="form.remark" :placeholder="t('sub.remarkPh')" />

          <!-- VPS：IP 地址（选填） -->
          <template v-if="isVpsCategory">
            <label for="sf-ipv4">{{ t('sub.ipLabel') }}</label>
            <div class="row">
              <div style="flex:1">
                <input id="sf-ipv4" v-model="form.ipv4" :placeholder="t('sub.ipv4')" />
              </div>
              <div style="flex:1">
                <input v-model="form.ipv6" :aria-label="t('sub.ipv6')" :placeholder="t('sub.ipv6')" />
              </div>
            </div>
          </template>

          <button class="btn ghost sm browse-btn" @click="openBrowser"><span class="i" v-html="icon('library')"></span>{{ t('sub.browse') }}</button>

          <details class="icon-lib">
            <summary>{{ t('sub.icon') }} — {{ t('sub.iconLibrary') }} / URL / {{ t('sub.uploadIcon') }}</summary>
            <input v-model="form.icon" :aria-label="t('sub.icon')" placeholder="emoji / /static/... / https://..." style="margin:8px 0" />
            <div class="row" style="margin-bottom:8px">
              <input v-model="iconUrl" :aria-label="t('sub.iconUrl')" :placeholder="t('sub.iconUrl')" style="flex:1" />
              <button class="btn ghost sm" @click="importIconUrl">{{ t('sub.iconUrlImport') }}</button>
              <label class="btn ghost sm" style="width:auto">{{ t('sub.uploadIcon') }}
                <input type="file" accept="image/*" hidden @change="uploadIcon" />
              </label>
            </div>
            <div class="lib-grid">
              <button v-for="it in iconLib" :key="it.slug" type="button" class="lib-ico" :title="it.name"
                      :aria-label="it.name" :aria-pressed="form.icon === it.icon" @click="form.icon = it.icon">
                <img :src="it.icon" alt="" loading="lazy" />
              </button>
            </div>
          </details>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secPrice') }}</div>
          <div class="row">
            <div style="flex:1">
              <label for="sf-amount">{{ t('sub.amount') }}</label>
              <input id="sf-amount" v-model.number="form.amount" type="number" step="0.01" />
            </div>
            <div style="flex:1">
              <label for="sf-currency">{{ t('sub.currency') }}</label>
              <select id="sf-currency" v-model="form.currency">
                <option v-for="c in currencies" :key="c.code" :value="c.code">{{ c.code }} {{ c.symbol }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secBilling') }}</div>
          <div class="row">
            <div style="flex:1">
              <label for="sf-billing">{{ t('sub.billingType') }}</label>
              <select id="sf-billing" v-model="form.billing_type">
                <option value="recurring">{{ t('sub.recurring') }}</option>
                <option value="one_time">{{ t('sub.oneTime') }}</option>
              </select>
            </div>
            <template v-if="form.billing_type === 'recurring'">
              <div style="flex:1">
                <label for="sf-cycle-count">{{ t('sub.cycleCount') }}</label>
                <input id="sf-cycle-count" v-model.number="form.cycle_count" type="number" min="1" />
              </div>
              <div style="flex:1">
                <label for="sf-cycle">{{ t('sub.cycle') }}</label>
                <select id="sf-cycle" v-model="form.cycle">
                  <option value="day">{{ t('sub.day') }}</option>
                  <option value="week">{{ t('sub.week') }}</option>
                  <option value="month">{{ t('sub.month') }}</option>
                  <option value="year">{{ t('sub.year') }}</option>
                </select>
              </div>
            </template>
          </div>
          <div class="row">
            <div style="flex:1">
              <label for="sf-start">{{ t('sub.startDate') }}</label>
              <input id="sf-start" v-model="form.start_date" type="date" />
            </div>
            <div style="flex:1" v-if="form.billing_type === 'recurring'">
              <label for="sf-next">{{ t('sub.nextRenewal') }}</label>
              <input id="sf-next" v-model="form.next_renewal_date" type="date" />
            </div>
          </div>
          <div class="row" v-if="form.billing_type === 'recurring'">
            <div style="flex:1">
              <label for="sf-remind">{{ t('sub.remindDays') }}</label>
              <input id="sf-remind" v-model="form.remind_days_before" placeholder="7,6,5,4,3,2,1" />
            </div>
            <div style="flex:1">
              <label for="sf-active">{{ t('sub.active') }}</label>
              <select id="sf-active" v-model="form.is_active"><option :value="true">{{ t('sub.yes') }}</option><option :value="false">{{ t('sub.no') }}</option></select>
            </div>
            <div style="flex:1">
              <label for="sf-auto">{{ t('sub.autoRenew') }}</label>
              <select id="sf-auto" v-model="form.auto_renew"><option :value="true">{{ t('sub.yes') }}</option><option :value="false">{{ t('sub.no') }}</option></select>
            </div>
          </div>
        </div>

        <div class="block" v-if="form.billing_type === 'recurring'">
          <div class="block-t">{{ t('sub.secTrialCard') }}</div>
          <div class="row">
            <div style="flex:1"><label for="sf-trial">{{ t('sub.trialEnd') }}</label><input id="sf-trial" type="date" v-model="form.trial_end" /></div>
            <div style="flex:1"><label for="sf-cancel-by">{{ t('sub.cancelBy') }}</label><input id="sf-cancel-by" type="date" v-model="form.cancel_by" /></div>
          </div>
          <div class="row">
            <div style="flex:1"><label for="sf-card4">{{ t('sub.cardLast4') }}</label><input id="sf-card4" v-model="form.card_last4" maxlength="4" placeholder="4242" /></div>
            <div style="flex:1"><label for="sf-card-exp">{{ t('sub.cardExpiry') }}</label><input id="sf-card-exp" v-model="form.card_expiry" placeholder="MM/YY" /></div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secClassify') }}</div>
          <div class="row">
            <div style="flex:1">
              <label for="sf-cat">{{ t('sub.category') }}</label>
              <select id="sf-cat" v-model="form.category_id">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
              </select>
            </div>
            <div style="flex:1">
              <label for="sf-pay">{{ t('sub.payment') }}</label>
              <select id="sf-pay" v-model="form.payment_method_id">
                <option :value="null">—</option>
                <option v-for="p in methods" :key="p.id" :value="p.id">{{ p.icon }} {{ p.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secFamily') }}</div>
          <div class="chips">
            <span v-for="(m, i) in form.family_members" :key="i" class="chip">
              {{ m }} <button class="chip-x" :aria-label="t('sub.delete')" @click="form.family_members.splice(i, 1)" v-html="icon('x')"></button>
            </span>
          </div>
          <div class="row">
            <input v-model="newMember" :aria-label="t('sub.familyPh')" :placeholder="t('sub.familyPh')" @keyup.enter="addMember" style="flex:1" />
            <button class="btn ghost sm" @click="addMember">{{ t('sub.familyAdd') }}</button>
          </div>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secBundle') }}</div>
          <div class="row radio-row">
            <label class="rb"><input type="radio" value="none" v-model="bundleMode" /> {{ t('sub.bundleNone') }}</label>
            <label class="rb"><input type="radio" value="join" v-model="bundleMode" /> {{ t('sub.bundleJoin') }}</label>
            <label class="rb"><input type="radio" value="create" v-model="bundleMode" /> {{ t('sub.bundleCreate') }}</label>
          </div>
          <select v-if="bundleMode === 'join'" :aria-label="t('sub.bundleJoin')" v-model="form.bundle_id">
            <option :value="null">—</option>
            <option v-for="b in bundles" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
          <input v-if="bundleMode === 'create'" v-model="newBundleName" :aria-label="t('sub.bundleName')" :placeholder="t('sub.bundleName')" />
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secExtra') }}</div>
          <label for="sf-url">{{ t('sub.website') }}</label>
          <input id="sf-url" v-model="form.url" placeholder="https://..." />
          <label for="sf-notes">{{ t('sub.notes') }}</label>
          <textarea id="sf-notes" v-model="form.notes" rows="2"></textarea>
        </div>

        <div class="block">
          <div class="block-t">{{ t('sub.secCalendar') }}</div>
          <label class="rb"><input type="checkbox" v-model="form.show_in_calendar" /> {{ t('sub.showInCalendar') }}</label>
        </div>

        <p v-if="formErr" ref="formErrEl" class="err" role="alert" tabindex="-1">{{ formErr }}</p>
        <div class="row" style="justify-content:flex-end;margin-top:16px">
          <button class="btn ghost" @click="showForm = false">{{ t('sub.cancel') }}</button>
          <button class="btn" :disabled="saving" @click="save">{{ t('sub.save') }}</button>
        </div>
    </BaseModal>

    <!-- 按分类浏览服务库 -->
    <BaseModal v-if="showBrowser" mask-class="browser" @close="showBrowser = false" v-slot="{ titleId }">
        <div class="browser-head">
          <h3 :id="titleId" style="margin:0">{{ t('sub.browseTitle') }}</h3>
          <button class="btn ghost sm" @click="showBrowser = false">{{ t('common.close') }}</button>
        </div>
        <p class="muted" style="font-size:13px;margin-top:0">{{ t('sub.pickHint') }}</p>
        <input v-model="browserQ" type="search" :aria-label="t('sub.searchPh')" :placeholder="t('sub.searchPh')" style="margin-bottom:12px" />
        <div v-for="g in groupedLib" :key="g.key" class="lib-group">
          <div class="lib-group-t">{{ g.label }}</div>
          <div class="svc-grid">
            <button v-for="s in g.items" :key="s.slug" class="svc" @click="pickFromBrowser(s)">
              <img :src="s.icon" alt="" class="svc-ico" /> <span>{{ s.name }}</span>
            </button>
          </div>
        </div>
        <p v-if="!groupedLib.length" class="muted">{{ t('reports.empty') }}</p>
    </BaseModal>

    <div class="toast-wrap" role="status" aria-live="polite">
      <div v-for="tst in toasts" :key="tst.id" class="toast" :class="tst.type"
           :role="tst.type === 'err' ? 'alert' : null">{{ tst.msg }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuth } from '../stores/auth'
import { icon } from '../icons'
import { daysLeft, isImg, lifeBar, statusOf } from '../lifeline'
import SubIcon from '../components/SubIcon.vue'
import BaseModal from '../components/BaseModal.vue'

const { t } = useI18n()
const auth = useAuth()
const subs = ref([])
const currencies = ref([])
const categories = ref([])
const methods = ref([])
const bundles = ref([])
const iconLib = ref([])
const filter = ref('')
const showForm = ref(false)
const formErr = ref('')
const formErrEl = ref(null)
const saving = ref(false)
const form = ref({})
const newMember = ref('')
const iconUrl = ref('')
const bundleMode = ref('none')
const newBundleName = ref('')
const suggestions = ref([])

const showBrowser = ref(false)
const browserQ = ref('')

const renewTarget = ref(null)
const renewBulk = ref(false)
const renewMode = ref('today')
const renewing = ref(false)

const delTarget = ref(null)
const delBulk = ref(false)
const delPwd = ref('')
const delErr = ref('')
const deleting = ref(false)

// 管理模式：'' 常规 | 'sort' 按钮排序（键盘 / 触屏可用） | 'select' 多选批量操作
const manage = ref('')
const selected = reactive(new Set())
const bulkBusy = ref(false)

const toasts = ref([])
let toastId = 0
function toast(msg, type = 'ok') {
  const id = ++toastId
  toasts.value.push({ id, msg, type })
  setTimeout(() => { toasts.value = toasts.value.filter((x) => x.id !== id) }, 2600)
}

function payName(s) {
  const p = methods.value.find((x) => x.id === s.payment_method_id)
  return p ? `${p.icon || ''} ${p.name}`.trim() : ''
}
function cycleText(s) {
  const n = s.cycle_count > 1 ? s.cycle_count + ' ' : ''
  return n + t('sub.' + s.cycle)
}
function dueText(s) {
  const d = daysLeft(s)
  if (d === null) return ''
  if (d < 0) return t('dashboard.overdueDays', { n: -d })
  return d === 0 ? t('dashboard.today') : t('dashboard.daysLeft', { n: d })
}
function lifeAttrs(s, i) {
  const b = lifeBar(s, i)
  return { class: b.cls, style: b.style }
}
const lateN = computed(() => subs.value.filter((s) => statusOf(s) === 'late').length)
const soonN = computed(() => subs.value.filter((s) => statusOf(s) === 'soon').length)

/* ---------- 客户端续费日计算（与后端 billing.add_cycle 对齐） ---------- */
function addMonths(d, months) {
  const base = new Date(d)
  const day = base.getDate()
  const target = new Date(base.getFullYear(), base.getMonth() + months, 1)
  const dim = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate()
  target.setDate(Math.min(day, dim))
  return target
}
function addCycle(dateStr, cycle, count) {
  const n = Math.max(1, count || 1)
  const d = new Date(dateStr)
  if (cycle === 'day') { d.setDate(d.getDate() + n); return d }
  if (cycle === 'week') { d.setDate(d.getDate() + n * 7); return d }
  if (cycle === 'year') return addMonths(d, n * 12)
  return addMonths(d, n)
}
function toISO(d) {
  const x = new Date(d)
  return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`
}

function blank() {
  return {
    id: null, name: '', plan: '', icon: '', amount: 0, currency: 'CNY',
    category_id: null, payment_method_id: null, bundle_id: null, billing_type: 'recurring',
    cycle: 'month', cycle_count: 1, start_date: new Date().toISOString().slice(0, 10),
    next_renewal_date: '', end_date: null, url: '', notes: '', remark: '', ipv4: '', ipv6: '',
    remind_days_before: '7,6,5,4,3,2,1', auto_renew: true, is_active: true,
    show_in_calendar: true, family_members: [],
    trial_end: null, cancel_by: null, card_last4: '', card_expiry: ''
  }
}

let suppressAuto = false
function recomputeNext() {
  if (form.value.billing_type !== 'recurring') { form.value.next_renewal_date = ''; return }
  if (form.value.start_date) {
    form.value.next_renewal_date = toISO(addCycle(form.value.start_date, form.value.cycle, form.value.cycle_count))
  }
}
watch(
  () => [form.value.start_date, form.value.cycle, form.value.cycle_count, form.value.billing_type],
  () => { if (!suppressAuto && showForm.value) recomputeNext() }
)

/* ---------- 分组与拖拽排序 ---------- */
// orderMap: { catKey: [subId, ...] } ; catOrder: [catKey, ...]
const orderMap = reactive({})
const catOrder = ref([])
const NONE = 'none'

function catKeyOf(s) { return s.category_id == null ? NONE : String(s.category_id) }
function catMeta(key) {
  if (key === NONE) return { icon: '', name: t('sub.uncategorized') }
  const c = categories.value.find((x) => String(x.id) === key)
  return c ? { icon: c.icon || '', name: c.name } : { icon: '', name: key }
}

function rebuild() {
  Object.keys(orderMap).forEach((k) => delete orderMap[k])
  const byCat = {}
  for (const s of subs.value) {
    const k = catKeyOf(s)
    ;(byCat[k] ||= []).push(s)
  }
  for (const k of Object.keys(byCat)) {
    byCat[k].sort((a, b) => (a.sort - b.sort) || (a.id - b.id))
    orderMap[k] = byCat[k].map((s) => s.id)
  }
  // 分类顺序：用户保存的顺序 → 其余出现的分类 → 未分类置底
  const present = new Set(Object.keys(orderMap))
  const saved = (auth.user?.category_order || []).map(String)
  const order = []
  for (const k of saved) if (present.has(k)) { order.push(k); present.delete(k) }
  const rest = [...present].filter((k) => k !== NONE)
    .sort((a, b) => {
      const ca = categories.value.find((x) => String(x.id) === a)
      const cb = categories.value.find((x) => String(x.id) === b)
      return ((ca?.sort ?? 999) - (cb?.sort ?? 999)) || (Number(a) - Number(b))
    })
  order.push(...rest)
  if (present.has(NONE)) order.push(NONE)
  catOrder.value = order
}

const search = ref('')
const grouped = computed(() => {
  const q = search.value.trim().toLowerCase()
  const match = (s) => !q || [s.name, s.plan, s.remark, s.url].some((v) => (v || '').toLowerCase().includes(q))
  return catOrder.value
    .filter((k) => orderMap[k] && orderMap[k].length)
    .map((k) => {
      const meta = catMeta(k)
      const items = orderMap[k].map((id) => subs.value.find((s) => s.id === id)).filter(Boolean).filter(match)
      return { key: k, icon: meta.icon, name: meta.name, items }
    })
    .filter((g) => g.items.length)  // 搜索时隐藏空分类
})

// 拖拽状态
let dragCatKey = null
let dragCard = null
const dragOverCat = ref(null)
const dragOverSub = ref(null)
function clearDrag() { dragCatKey = null; dragCard = null; dragOverCat.value = null; dragOverSub.value = null }

function onCatDragStart(key, e) {
  // 仅当不是从卡片发起时才作为分类拖拽
  if (dragCard) return
  dragCatKey = key
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}
function onCatDragOver(key) { if (dragCatKey && !dragCard) dragOverCat.value = key }
async function onCatDrop(key) {
  if (!dragCatKey || dragCard || dragCatKey === key) return clearDrag()
  const arr = [...catOrder.value]
  const from = arr.indexOf(dragCatKey)
  const to = arr.indexOf(key)
  if (from < 0 || to < 0) return clearDrag()
  arr.splice(to, 0, arr.splice(from, 1)[0])
  clearDrag()
  saveCatOrder(arr)
}
async function saveCatOrder(arr) {
  catOrder.value = arr
  // 持久化（只保存真实分类 id，未分类不存）
  const ids = arr.filter((k) => k !== NONE).map(Number)
  try { await auth.updateMe({ category_order: ids }) } catch { /* ignore */ }
}
async function saveSubOrder(catKey, arr) {
  orderMap[catKey] = arr
  try { await api.post('/api/subscriptions/reorder', { ordered_ids: arr }) } catch { /* ignore */ }
}

/* ---------- 排序模式：上移 / 下移（拖拽的键盘与触屏替代） ---------- */
function canMoveCatDown(key) {
  const arr = catOrder.value
  const next = arr[arr.indexOf(key) + 1]
  return next !== undefined && next !== NONE
}
function moveCat(key, dir) {
  const arr = [...catOrder.value]
  const from = arr.indexOf(key)
  const to = from + dir
  if (from < 0 || to < 0 || to >= arr.length || arr[to] === NONE) return
  ;[arr[from], arr[to]] = [arr[to], arr[from]]
  keepFocus(() => saveCatOrder(arr))
}
function moveSub(catKey, id, dir) {
  const arr = [...orderMap[catKey]]
  const from = arr.indexOf(id)
  const to = from + dir
  if (from < 0 || to < 0 || to >= arr.length) return
  ;[arr[from], arr[to]] = [arr[to], arr[from]]
  keepFocus(() => saveSubOrder(catKey, arr))
}
// 换位时 Vue 会移动 DOM 节点，被移动的按钮会失去焦点；重排后按 aria-label 找回同一个按钮。
// 若它移到了边界而被禁用，就聚焦旁边那个反方向按钮，保证键盘用户能连续操作。
function keepFocus(reorder) {
  const label = document.activeElement?.getAttribute('aria-label')
  reorder()
  if (!label) return
  nextTick(() => {
    const btn = [...document.querySelectorAll('.subs button[aria-label]')].find((b) => b.getAttribute('aria-label') === label)
    if (!btn) return
    if (!btn.disabled) btn.focus()
    else [...btn.parentElement.querySelectorAll('button')].find((b) => b !== btn && !b.disabled)?.focus()
  })
}

function setManage(m) {
  manage.value = manage.value === m ? '' : m
  selected.clear()
  // 排序按完整列表计算，搜索过滤会让「上移」看起来没反应，进入排序时清空搜索
  if (manage.value === 'sort') search.value = ''
}

function onCardDragStart(catKey, id, e) {
  dragCard = { catKey, id }
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}
function onCardDragOver(catKey, id) {
  if (dragCard && dragCard.catKey === catKey) dragOverSub.value = id
}
async function onCardDrop(catKey, id) {
  if (!dragCard || dragCard.catKey !== catKey || dragCard.id === id) return clearDrag()
  const arr = [...orderMap[catKey]]
  const from = arr.indexOf(dragCard.id)
  const to = arr.indexOf(id)
  if (from < 0 || to < 0) return clearDrag()
  arr.splice(to, 0, arr.splice(from, 1)[0])
  orderMap[catKey] = arr
  clearDrag()
  try { await api.post('/api/subscriptions/reorder', { ordered_ids: arr }) } catch { /* ignore */ }
}

async function load() {
  const params = filter.value ? { billing_type: filter.value } : {}
  const { data } = await api.get('/api/subscriptions', { params })
  subs.value = data
  rebuild()
  // 已删除或被筛选掉的订阅不再保留选中
  const ids = new Set(data.map((s) => s.id))
  for (const id of [...selected]) if (!ids.has(id)) selected.delete(id)
}
function setFilter(f) { filter.value = f; load() }

function openNew() {
  form.value = blank(); formErr.value = ''; bundleMode.value = 'none'
  newBundleName.value = ''; suggestions.value = []; showForm.value = true
  recomputeNext()
}
function openEdit(s) {
  suppressAuto = true
  form.value = { ...s, next_renewal_date: s.next_renewal_date || '', family_members: s.family_members || [] }
  formErr.value = ''; suggestions.value = []
  bundleMode.value = s.bundle_id ? 'join' : 'none'
  newBundleName.value = ''
  showForm.value = true
  nextTick(() => { suppressAuto = false })
}

function onNameInput() {
  const q = (form.value.name || '').toLowerCase().trim()
  suggestions.value = q.length < 1 ? []
    : iconLib.value.filter((s) => s.name.toLowerCase().includes(q)).slice(0, 6)
}
// 服务库分类 key -> 在用户分类名中查找的关键字
const CAT_KEYWORDS = {
  streaming: 'streaming', music: 'music', ai: 'ai', gaming: 'gaming', vps: 'vps',
  carrier: 'carrier', cloud: 'cloud', software: 'software', domain: 'domain',
  education: 'education', news: 'news', fitness: 'fitness', membership: 'membership'
}
function findCategoryByKey(key) {
  const kw = CAT_KEYWORDS[key]
  if (!kw) return null
  const hit = categories.value.find((c) => (c.name || '').toLowerCase().includes(kw))
  return hit ? hit.id : null
}
const isVpsCategory = computed(() => {
  const c = categories.value.find((x) => x.id === form.value.category_id)
  if (!c) return false
  return (c.name || '').toLowerCase().includes('vps') || (c.name || '').includes('服务器')
})

function pickService(s) {
  form.value.name = s.name
  form.value.icon = s.icon
  if (!form.value.url && s.website) form.value.url = s.website
  // 自动带出分类（按服务库分类映射到用户分类）
  if (s.category) {
    const cid = findCategoryByKey(s.category)
    if (cid) form.value.category_id = cid
  }
  suggestions.value = []
}
// 联想列表打开时，Esc 只关列表，不关整个弹窗
function closeSuggest(e) {
  if (!suggestions.value.length) return
  e.stopPropagation()
  suggestions.value = []
}

function openBrowser() { browserQ.value = ''; showBrowser.value = true }
const groupedLib = computed(() => {
  const q = browserQ.value.toLowerCase().trim()
  const groups = new Map()
  for (const s of iconLib.value) {
    if (q && !s.name.toLowerCase().includes(q)) continue
    const key = s.category || 'other'
    if (!groups.has(key)) groups.set(key, { key, label: s.category_label || key, items: [] })
    groups.get(key).items.push(s)
  }
  return [...groups.values()]
})
function pickFromBrowser(s) { pickService(s); showBrowser.value = false }

function addMember() {
  const v = newMember.value.trim()
  if (v) { form.value.family_members.push(v); newMember.value = '' }
}

async function importIconUrl() {
  if (!iconUrl.value.trim()) return
  try {
    const { data } = await api.post('/api/icons/from-url', { url: iconUrl.value.trim() })
    form.value.icon = data.url; iconUrl.value = ''
  } catch (e) { formErr.value = e.response?.data?.detail || 'Error' }
}
async function uploadIcon(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post('/api/icons/upload', fd)
    form.value.icon = data.url
  } catch (err) { formErr.value = err.response?.data?.detail || 'Error' } finally { e.target.value = '' }
}

async function exportCsv() {
  try {
    const { data } = await api.get('/api/subscriptions/export.csv', { responseType: 'text' })
    const blob = new Blob([data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'easysub-subscriptions.csv'
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  } catch (e) { toast(e.response?.data?.detail || 'Error', 'err') }
}
async function importCsv(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const content = await file.text()
    const { data } = await api.post('/api/subscriptions/import-csv', { content })
    toast(t('sub.csvImported', { n: data.imported }))
    load()
  } catch (err) { toast(err.response?.data?.detail || 'Error', 'err') } finally { e.target.value = '' }
}

async function save() {
  if (saving.value) return
  saving.value = true
  formErr.value = ''
  try {
    if (bundleMode.value === 'create' && newBundleName.value.trim()) {
      const { data } = await api.post('/api/bundles', { name: newBundleName.value.trim() })
      form.value.bundle_id = data.id
      bundles.value.push(data)
    } else if (bundleMode.value === 'none') {
      form.value.bundle_id = null
    }
    const payload = { ...form.value }
    if (!payload.next_renewal_date) delete payload.next_renewal_date
    // 空日期串转 null，避免后端日期解析报错
    for (const k of ['trial_end', 'cancel_by']) if (!payload[k]) payload[k] = null
    for (const k of ['card_last4', 'card_expiry']) if (!payload[k]) payload[k] = null
    if (payload.id) await api.put(`/api/subscriptions/${payload.id}`, payload)
    else await api.post('/api/subscriptions', payload)
    showForm.value = false
    toast(t('settings.saved'))
    load()
  } catch (e) {
    formErr.value = e.response?.data?.detail || 'Error'
    // 表单很长，把焦点送到错误提示上（同时滚动到可见处），读屏也会立即播报
    await nextTick()
    formErrEl.value?.focus()
  } finally {
    saving.value = false
  }
}

/* ---------- 续费 ---------- */
function askRenew(s) { renewTarget.value = s; renewBulk.value = false; renewMode.value = 'today' }
function closeRenew() { renewTarget.value = null; renewBulk.value = false }
const previewToday = computed(() =>
  renewTarget.value ? toISO(addCycle(new Date(), renewTarget.value.cycle, renewTarget.value.cycle_count)) : ''
)
const previewDue = computed(() => {
  if (!renewTarget.value) return ''
  const base = renewTarget.value.next_renewal_date ? new Date(renewTarget.value.next_renewal_date) : new Date()
  return toISO(addCycle(base, renewTarget.value.cycle, renewTarget.value.cycle_count))
})
async function confirmRenew() {
  if (renewBulk.value) return confirmBulkRenew()
  if (!renewTarget.value || renewing.value) return
  renewing.value = true
  try {
    const { data } = await api.post(`/api/subscriptions/${renewTarget.value.id}/renew`, { mode: renewMode.value })
    toast(t('sub.renewOk', { date: data.next_renewal_date }))
    renewTarget.value = null
    load()
  } catch (e) {
    toast(e.response?.data?.detail || 'Error', 'err')
  } finally {
    renewing.value = false
  }
}

function askDelete(s) { delTarget.value = s; delBulk.value = false; delPwd.value = ''; delErr.value = '' }
function closeDelete() { delTarget.value = null; delBulk.value = false }
async function confirmDelete() {
  if (delBulk.value) return confirmBulkDelete()
  if (!delTarget.value || deleting.value || !delPwd.value) return
  deleting.value = true
  delErr.value = ''
  try {
    await api.delete(`/api/subscriptions/${delTarget.value.id}`, { data: { password: delPwd.value } })
    delTarget.value = null
    toast(t('sub.delete'))
    load()
  } catch (e) {
    delErr.value = e.response?.data?.detail || 'Error'
  } finally {
    deleting.value = false
  }
}

/* ---------- 多选与批量操作（逐个调用现有接口，后端无需改动） ---------- */
function toggleSel(id) { selected.has(id) ? selected.delete(id) : selected.add(id) }
function toggleGroup(g) {
  const all = g.items.every((s) => selected.has(s.id))
  for (const s of g.items) all ? selected.delete(s.id) : selected.add(s.id)
}
const visibleIds = computed(() => grouped.value.flatMap((g) => g.items.map((s) => s.id)))
const allVisibleSelected = computed(() => visibleIds.value.length > 0 && visibleIds.value.every((id) => selected.has(id)))
function toggleAllVisible() {
  const all = allVisibleSelected.value
  for (const id of visibleIds.value) all ? selected.delete(id) : selected.add(id)
}
const selectedRecurring = computed(() =>
  subs.value.filter((s) => selected.has(s.id) && s.billing_type === 'recurring').map((s) => s.id))

// 顺序执行，避免一次性打满后端；done 为调用前已完成的数量（批量删除先删了一个校验密码）
async function runBulk(ids, fn, done = 0) {
  bulkBusy.value = true
  let ok = done
  let fail = 0
  try {
    for (const id of ids) {
      try { await fn(id); ok++ } catch { fail++ }
    }
  } finally {
    bulkBusy.value = false
  }
  toast(fail ? t('sub.bulkPartial', { ok, fail }) : t('sub.bulkDone', { n: ok }), fail ? 'err' : 'ok')
  await load()
  return { ok, fail }
}

function askBulkRenew() { renewTarget.value = null; renewBulk.value = true; renewMode.value = 'today' }
async function confirmBulkRenew() {
  if (renewing.value) return
  renewing.value = true
  const ids = [...selectedRecurring.value]
  const mode = renewMode.value
  closeRenew()
  try { await runBulk(ids, (id) => api.post(`/api/subscriptions/${id}/renew`, { mode })) } finally { renewing.value = false }
}
function bulkSetActive(active) {
  runBulk([...selected], (id) => api.put(`/api/subscriptions/${id}`, { is_active: active }))
}
function bulkSetCategory(e) {
  const v = e.target.value
  e.target.value = ''
  if (!v) return
  const category_id = v === 'none' ? null : Number(v)
  runBulk([...selected], (id) => api.put(`/api/subscriptions/${id}`, { category_id }))
}

function askBulkDelete() { delTarget.value = null; delBulk.value = true; delPwd.value = ''; delErr.value = '' }
async function confirmBulkDelete() {
  if (deleting.value || !delPwd.value) return
  deleting.value = true
  delErr.value = ''
  const ids = [...selected]
  const password = delPwd.value
  try {
    // 先删第一个来校验密码：密码错就停在弹窗里提示，不会对每一项都报一次错
    await api.delete(`/api/subscriptions/${ids[0]}`, { data: { password } })
    closeDelete()
    const { fail } = await runBulk(ids.slice(1), (id) => api.delete(`/api/subscriptions/${id}`, { data: { password } }), 1)
    if (!fail) selected.clear()
  } catch (e) {
    delErr.value = e.response?.data?.detail || 'Error'
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  const [c, cat, m, b, lib] = await Promise.all([
    api.get('/api/currencies'),
    api.get('/api/categories'),
    api.get('/api/payment-methods'),
    api.get('/api/bundles'),
    api.get('/api/icons/library')
  ])
  currencies.value = c.data
  categories.value = cat.data
  methods.value = m.data
  bundles.value = b.data
  iconLib.value = lib.data
  load()
})
</script>

<style scoped>
.i { display: inline-flex; width: 16px; height: 16px; flex-shrink: 0; }
.i :deep(svg) { width: 100%; height: 100%; }
.err { color: var(--late); font-size: 13px; }
.ico { width: 18px; height: 18px; vertical-align: middle; border-radius: 4px; }

.lede { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 6px !important; }
.lede span { display: inline-flex; align-items: center; gap: 7px; font-weight: 550; }
.lede span::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.lede-late { color: var(--late); }
.lede-soon { color: var(--soon); }
.lede-ok { color: var(--ok); }

/* ---------- 工具栏 ---------- */
.toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.search { position: relative; flex: 1; min-width: 180px; max-width: 360px; margin: 0; }
.search .i { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--text-faint); pointer-events: none; }
.search input { padding-left: 34px; min-height: 38px; }
.tb-right { display: flex; gap: 8px; margin-left: auto; }
.tb-right label.btn { margin: 0; color: var(--text); }
.drag-hint { display: flex; align-items: center; gap: 6px; font-size: 12.5px; margin: 10px 0 18px; }
.drag-hint .i { width: 14px; height: 14px; }
.tb-right .btn.on { background: var(--primary-soft); border-color: var(--primary); color: var(--text); }
.mode-hint { color: var(--text); }

/* ---------- 多选批量操作条 ---------- */
.bulk-bar { position: sticky; bottom: 16px; z-index: 20; display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  margin-top: 8px; padding: 10px 12px; background: var(--surface); border: 1px solid var(--border-strong);
  border-radius: var(--radius); box-shadow: var(--shadow-lg); }
.bulk-n { font-weight: 650; font-size: 14px; padding: 0 4px; }
.bulk-sep { flex: 1; }
.bulk-cat { width: auto; min-height: 32px; padding: 4px 10px; font-size: 13px; }
.sub-card.picked { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft), var(--shadow); }
.sc-check { flex-shrink: 0; width: 20px; height: 20px; margin: 0; cursor: pointer; }

/* ---------- 分类分组 ---------- */
.cat-group { margin-bottom: 28px; border-radius: var(--radius); outline: 2px dashed transparent; outline-offset: 6px;
  transition: outline-color .12s; }
.cat-group.drop-cat { outline-color: var(--primary); }
.cat-head { display: flex; align-items: center; gap: 9px; margin-bottom: 12px; cursor: grab; }
.cat-head .grip { width: 16px; height: 16px; display: inline-flex; color: var(--text-faint); }
.cat-ico { font-size: 18px; line-height: 1; }
.cat-name { font-size: 17px; font-weight: 650; margin: 0; letter-spacing: -.01em; }
.cat-line { flex: 1; height: 1px; background: var(--border); }

/* ---------- 订阅卡 ---------- */
.sub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.sub-card { position: relative; display: flex; flex-direction: column; gap: 12px; padding: 18px 18px 14px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
  cursor: grab; transition: transform .25s var(--ease-out), box-shadow .25s var(--ease-out), border-color .2s; }
.sub-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); border-color: var(--border-strong); }
.sub-card:hover :deep(.sub-icon) { transform: scale(1.06); }
.sub-card :deep(.sub-icon) { transition: transform .3s var(--ease-out); }
.sub-card:active { cursor: grabbing; }
.sub-card:not([draggable="true"]) { cursor: default; }
.cat-group:not([draggable="true"]) .cat-head { cursor: default; }
.sub-card.inactive { opacity: .55; }
.sub-card.drop-card { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft); }
/* 过期：整张卡转为警示色，一眼可见 */
.sub-card.is-late { background: linear-gradient(var(--late-soft), var(--late-soft)) padding-box, var(--surface);
  border-color: color-mix(in srgb, var(--late) 45%, var(--border)); }
.sub-card.is-late:hover { border-color: var(--late); }
.sub-card.is-soon { border-color: color-mix(in srgb, var(--soon-bar) 60%, var(--border)); }
.sub-card.is-soon:hover { border-color: var(--soon-bar); }

.sc-head { display: flex; align-items: center; gap: 12px; }
.sc-title { flex: 1; min-width: 0; }
.sc-name { font-weight: 650; font-size: 16.5px; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-plan { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-head .tag { flex-shrink: 0; }
.sc-head .tag .i { width: 13px; height: 13px; }
.sc-remark { margin: 0; padding: 7px 10px; border-radius: 8px; font-size: 13px; line-height: 1.45;
  background: var(--surface-2); color: var(--text); overflow-wrap: anywhere; }
.is-late .sc-remark { background: color-mix(in srgb, var(--surface) 70%, transparent); }

.sc-money { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
.sc-money .amt { font-size: 26px; font-weight: 650; letter-spacing: -.025em; }
.sc-money .cur { font-size: 14px; font-weight: 550; color: var(--text-soft); }
.sc-money .cycle { font-size: 14px; color: var(--text-soft); }

.sc-count { display: flex; flex-direction: column; gap: 6px; }
.sc-count-t { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; font-size: 13px; }
.sc-count .left { font-weight: 650; font-size: 14px; color: var(--ok); }
.sc-count .left.soon { color: var(--soon); }
.sc-count .left.late { color: var(--late); }
.sc-count .date { white-space: nowrap; }
.sc-count .life { height: 7px; }

.sc-facts { margin: 0; display: flex; flex-direction: column; gap: 5px; font-size: 13px; }
.sc-facts:empty { display: none; }
.sc-facts > div { display: flex; justify-content: space-between; gap: 12px; }
.sc-facts dt { color: var(--text-soft); flex-shrink: 0; }
.sc-facts dd { margin: 0; text-align: right; min-width: 0; overflow-wrap: anywhere; }
.mono { font-family: var(--mono); font-size: 12px; }
.yn { width: 15px; height: 15px; color: var(--text-faint); vertical-align: middle; }
.yn.on { color: var(--ok); }

.sc-acts { display: flex; gap: 8px; margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border); }
.sc-acts .btn:not(.icon) { flex: 1; }
.is-late .sc-acts { border-top-color: color-mix(in srgb, var(--late) 20%, var(--border)); }
.is-late .renew { background: var(--late); color: #fff; }

/* ---------- 续费弹窗 ---------- */
.opt { display: flex; align-items: flex-start; gap: 10px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px 14px; margin-top: 10px; cursor: pointer; font-size: 14px; color: var(--text); width: auto;
  transition: border-color .15s, background-color .15s; }
.opt:hover { border-color: var(--border-strong); }
.opt.on { border-color: var(--primary); background: var(--primary-soft); }
.opt input { margin-top: 3px; }
.opt-d { font-size: 12.5px; margin-top: 3px; }

/* ---------- 表单 ---------- */
.block { padding: 4px 0 16px; margin-bottom: 14px; border-bottom: 1px solid var(--border); }
.block:last-of-type { border-bottom: 0; }
.block-t { font-size: 14px; font-weight: 650; color: var(--text); margin-bottom: 2px; }
.icon-pick { display: flex; align-items: flex-end; padding-bottom: 1px; }
.browse-btn { margin-top: 10px; }
.suggest { position: absolute; z-index: 5; left: 0; right: 0; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm); box-shadow: var(--shadow-lg); margin-top: 4px; padding: 4px; }
.suggest-i { display: flex; align-items: center; gap: 8px; width: 100%; padding: 8px 10px; min-height: 38px; cursor: pointer;
  font: inherit; font-size: 14px; color: var(--text); text-align: left; border: 0; background: none; border-radius: 7px; }
.suggest-i:hover, .suggest-i:focus-visible { background: var(--surface-2); }
.icon-lib { margin-top: 10px; }
.icon-lib summary { cursor: pointer; font-size: 13px; color: var(--text-soft); padding: 6px 0; }
.icon-lib summary:hover { color: var(--text); }
.icon-lib .row label.btn { margin: 0; color: var(--text); }
.lib-grid { display: grid; grid-template-columns: repeat(auto-fill, 38px); gap: 6px; max-height: 160px; overflow: auto; }
.lib-ico { width: 38px; height: 38px; border-radius: 9px; padding: 6px; border: 1px solid var(--border); cursor: pointer;
  background: var(--surface); transition: border-color .12s, transform .12s; }
.lib-ico img { display: block; width: 100%; height: 100%; object-fit: contain; }
.lib-ico:hover, .lib-ico[aria-pressed="true"] { border-color: var(--primary); }
.lib-ico:hover { transform: scale(1.06); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.chips:empty { display: none; }
.chip { display: inline-flex; align-items: center; gap: 4px; background: var(--surface-2); color: var(--text);
  padding: 3px 4px 3px 10px; border-radius: 999px; font-size: 13px; }
.chip-x { width: 22px; height: 22px; display: inline-flex; padding: 5px; border: 0; border-radius: 50%; background: none;
  color: var(--text-soft); cursor: pointer; }
.chip-x:hover { background: var(--border); color: var(--text); }
.radio-row { gap: 18px; }
.rb { display: flex; align-items: center; gap: 8px; width: auto; margin: 6px 0; font-size: 14px; color: var(--text); cursor: pointer; }

/* ---------- 服务库 ---------- */
.browser .modal { width: 620px; }
.browser-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }
.lib-group { margin-bottom: 16px; }
.lib-group-t { font-size: 13px; font-weight: 600; color: var(--text-soft); margin-bottom: 8px; }
.svc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.svc { display: flex; align-items: center; gap: 9px; padding: 8px 10px; min-height: 42px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface); cursor: pointer; font: inherit; font-size: 13.5px;
  color: var(--text); text-align: left; transition: border-color .12s, background-color .12s, transform .12s; }
.svc:hover { border-color: var(--border-strong); background: var(--surface-2); transform: translateY(-1px); }
.svc-ico { width: 22px; height: 22px; border-radius: 5px; object-fit: contain; flex-shrink: 0; }
.svc span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 720px) {
  .search { max-width: none; order: 3; flex-basis: 100%; }
  .tb-right { margin-left: auto; flex-wrap: wrap; justify-content: flex-end; }
  .drag-hint:not(.mode-hint) { display: none; }
  .bulk-bar { bottom: calc(84px + env(safe-area-inset-bottom)); }
  .toolbar { margin-bottom: 20px; }
  .sub-grid { grid-template-columns: 1fr; gap: 12px; }
  .sub-card { padding: 16px 16px 12px; }
  .sub-card:hover { transform: none; }
  .sc-money .amt { font-size: 23px; }
  .svc-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }
}
</style>
