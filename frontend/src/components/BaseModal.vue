<!--
  通用弹窗外壳：只负责无障碍与键盘行为，样式沿用全局 .modal-mask / .modal。
  - role="dialog" + aria-modal，标题通过插槽参数 titleId 关联（<h3 :id="titleId">）
  - Esc 关闭、Tab 焦点限制在弹窗内、打开时聚焦第一个输入控件、关闭后焦点回到打开前的元素
  传给组件的 class / style 落在 .modal 上（如 style="width:460px"），遮罩额外的类用 mask-class。
-->
<template>
  <div class="modal-mask" :class="maskClass" @click.self="emit('close')">
    <div ref="box" class="modal" v-bind="$attrs" role="dialog" aria-modal="true" :aria-labelledby="titleId"
         tabindex="-1" @keydown="onKey">
      <slot :title-id="titleId" />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, useId } from 'vue'

defineOptions({ inheritAttrs: false })
defineProps({ maskClass: { type: [String, Array, Object], default: '' } })
const emit = defineEmits(['close'])

const titleId = useId()
const box = ref(null)
let opener = null

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])'
function focusables() {
  return [...box.value.querySelectorAll(FOCUSABLE)].filter((el) => el.getClientRects().length)
}

function onKey(e) {
  if (e.key === 'Escape') {
    e.stopPropagation()
    emit('close')
    return
  }
  if (e.key !== 'Tab') return
  const list = focusables()
  if (!list.length) { e.preventDefault(); return }
  const first = list[0]
  const last = list[list.length - 1]
  const cur = document.activeElement
  if (e.shiftKey && (cur === first || cur === box.value)) { e.preventDefault(); last.focus() }
  else if (!e.shiftKey && cur === last) { e.preventDefault(); first.focus() }
}

onMounted(async () => {
  opener = document.activeElement
  await nextTick()
  // 优先聚焦文本类输入；没有就聚焦弹窗本身，让读屏先读标题
  const field = box.value.querySelector('input:not([type="radio"]):not([type="checkbox"]):not([hidden]), textarea')
  ;(field || box.value).focus()
})
onBeforeUnmount(() => {
  if (opener && document.contains(opener)) opener.focus()
})
</script>
