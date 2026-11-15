<template>
  <div class="wheel-control">
  <button class="btn ghost wheel-step" :aria-label="decreaseLabel" :disabled="modelValue === options[0]" @click="settle(target - 1, $event.detail === 0)">−</button>
  <div class="inertia-wheel" role="spinbutton" tabindex="0" :aria-label="label" :aria-valuemin="options[0]" :aria-valuemax="options.at(-1)" :aria-valuenow="modelValue" :aria-valuetext="`${modelValue} ${unit}`"
    @pointerdown="start" @pointermove="move" @pointerup="release" @pointercancel="cancel" @lostpointercapture="cancel" @keydown="key" @wheel.prevent="wheel">
    <div class="wheel-band" aria-hidden="true"></div>
    <div class="wheel-track" :style="{ transform: `translateY(${66 - position * 44}px)` }" aria-hidden="true">
      <div v-for="(value,i) in options" :key="value" :class="{ chosen: Math.round(position) === i }">{{ value }} <small>{{ unit }}</small></div>
    </div>
  </div>
  <button class="btn ghost wheel-step" :aria-label="increaseLabel" :disabled="modelValue === options.at(-1)" @click="settle(target + 1, $event.detail === 0)">+</button>
  </div>
</template>
<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
const props = defineProps({ modelValue: Number, options: Array, label: String, unit: String, decreaseLabel: String, increaseLabel: String })
const emit = defineEmits(['update:modelValue'])
const position = ref(Math.max(0, props.options.indexOf(props.modelValue)))
let frame = 0, drag, target = position.value
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches
const clamp = n => Math.max(0, Math.min(props.options.length - 1, n))
function stop() { cancelAnimationFrame(frame); frame = 0 }
function settle(next, immediate = false) {
  stop(); target = clamp(Math.round(next))
  if (immediate || reduced()) { position.value = target; emit('update:modelValue', props.options[target]); return }
  let velocity = 0, last = performance.now()
  const tick = now => {
    const dt = Math.min((now - last) / 1000, .032); last = now
    velocity += ((target - position.value) * 210 - velocity * 25) * dt
    position.value += velocity * dt
    if (Math.abs(target - position.value) < .003 && Math.abs(velocity) < .02) {
      position.value = target; frame = 0; emit('update:modelValue', props.options[target])
    } else frame = requestAnimationFrame(tick)
  }
  frame = requestAnimationFrame(tick)
}
function start(e) { if (e.button !== 0) return; stop(); e.currentTarget.setPointerCapture(e.pointerId); drag = { y: e.clientY, start: e.clientY, p: position.value, time: e.timeStamp, velocity: 0 } }
function move(e) {
  if (!drag) return
  const raw = drag.p + (drag.start - e.clientY) / 44, edge = clamp(raw)
  position.value = edge + (raw - edge) * .22
  drag.velocity = (drag.y - e.clientY) / Math.max(8, e.timeStamp - drag.time) / 44
  drag.y = e.clientY; drag.time = e.timeStamp
}
function release(e) {
  if (!drag) return
  const velocity = e.timeStamp - drag.time > 90 ? 0 : drag.velocity
  const next = Math.abs(e.clientY - drag.start) < 5 ? position.value + (e.clientY - e.currentTarget.getBoundingClientRect().top - 88) / 44 : position.value + velocity * 160
  drag = null; settle(next)
}
function cancel() { if (!drag) return; drag = null; settle(position.value) }
function wheel(e) { settle(target + Math.sign(e.deltaY)) }
function key(e) {
  const next = { ArrowDown: target + 1, ArrowUp: target - 1, Home: 0, End: props.options.length - 1 }[e.key]
  if (next === undefined) return
  e.preventDefault(); settle(next, true)
}
watch(() => props.modelValue, value => { if (!drag) { stop(); target = Math.max(0, props.options.indexOf(value)); position.value = target } })
onBeforeUnmount(stop)
</script>
<style scoped>
.wheel-control { display:grid; grid-template-columns:48px minmax(0,1fr) 48px; gap:12px; min-width:0; align-items:center; }
.wheel-step { width:48px; min-height:48px; font-size:20px; border-radius:50%; }
.inertia-wheel { position: relative; height: 176px; overflow: hidden; touch-action: none; cursor: ns-resize; user-select: none; border-radius: var(--radius-sm); background: var(--surface); }
.inertia-wheel:focus-visible { outline: 2px solid var(--primary); outline-offset: 3px; }
.wheel-band { position: absolute; inset: 66px 12px; height: 44px; border-block: 1px solid var(--border-strong); background: var(--primary-soft); }
.wheel-track { position: relative; pointer-events: none; }
.wheel-track > div { height: 44px; display: flex; align-items: center; justify-content: center; gap: 8px; color: var(--text-soft); font-size: 20px; font-variant-numeric: tabular-nums; }
.wheel-track > .chosen { color: var(--text); font-weight: 650; }
small { font-size: 14px; font-weight: 400; }
</style>
