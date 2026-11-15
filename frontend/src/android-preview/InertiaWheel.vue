<template>
  <div class="wheel-control">
  <button class="btn ghost wheel-step" :aria-label="decreaseLabel" :disabled="modelValue === options[0]" @click="settle(target - 1, $event.detail === 0)">−</button>
  <div class="inertia-wheel" role="spinbutton" tabindex="0" :aria-label="label" :aria-valuemin="options[0]" :aria-valuemax="options.at(-1)" :aria-valuenow="modelValue" :aria-valuetext="`${modelValue} ${unit}`"
    @pointerdown="start" @pointermove="move" @pointerup="release" @pointercancel="cancel" @lostpointercapture="cancel" @keydown="key" @wheel.prevent="wheel">
    <div class="wheel-band" aria-hidden="true"></div>
    <div class="wheel-track" :style="{ transform: `translateY(${WHEEL_PHYSICS.bandTop - position * WHEEL_PHYSICS.row}px)` }" aria-hidden="true">
      <div v-for="(value,i) in options" :key="value" :class="{ chosen: Math.round(position) === i }">{{ value }} <small>{{ unit }}</small></div>
    </div>
  </div>
  <button class="btn ghost wheel-step" :aria-label="increaseLabel" :disabled="modelValue === options.at(-1)" @click="settle(target + 1, $event.detail === 0)">+</button>
  </div>
</template>
<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { WHEEL_PHYSICS, wheelStep } from './wheel-physics.js'
import { haptics } from './haptics.js'
const props = defineProps({ modelValue: Number, options: Array, label: String, unit: String, decreaseLabel: String, increaseLabel: String })
const emit = defineEmits(['update:modelValue'])
const position = ref(Math.max(0, props.options.indexOf(props.modelValue)))
let frame = 0, drag, target = position.value
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches
const clamp = n => Math.max(0, Math.min(props.options.length - 1, n))
function stop() { cancelAnimationFrame(frame); frame = 0 }
function settle(next, immediate = false) {
  stop(); target = clamp(Math.round(next))
  if (props.options[target] !== props.modelValue) haptics.tick()
  if (immediate || reduced()) { position.value = target; emit('update:modelValue', props.options[target]); return }
  let velocity = 0, last = performance.now()
  const tick = now => {
    const next = wheelStep({ position: position.value, velocity }, target, (now - last) / 1000); last = now
    velocity = next.velocity; position.value = next.position
    if (Math.abs(target - position.value) < WHEEL_PHYSICS.positionEpsilon && Math.abs(velocity) < WHEEL_PHYSICS.velocityEpsilon) {
      position.value = target; frame = 0; emit('update:modelValue', props.options[target])
    } else frame = requestAnimationFrame(tick)
  }
  frame = requestAnimationFrame(tick)
}
function start(e) { if (e.button !== 0) return; stop(); e.currentTarget.setPointerCapture(e.pointerId); drag = { y: e.clientY, start: e.clientY, p: position.value, time: e.timeStamp, velocity: 0 } }
function move(e) {
  if (!drag) return
  const raw = drag.p + (drag.start - e.clientY) / WHEEL_PHYSICS.row, edge = clamp(raw)
  position.value = edge + (raw - edge) * WHEEL_PHYSICS.edgeResistance
  drag.velocity = (drag.y - e.clientY) / Math.max(WHEEL_PHYSICS.minSampleMs, e.timeStamp - drag.time) / WHEEL_PHYSICS.row
  drag.y = e.clientY; drag.time = e.timeStamp
}
function release(e) {
  if (!drag) return
  const velocity = e.timeStamp - drag.time > WHEEL_PHYSICS.staleVelocityMs ? 0 : drag.velocity
  const next = Math.abs(e.clientY - drag.start) < WHEEL_PHYSICS.tapSlop ? position.value + (e.clientY - e.currentTarget.getBoundingClientRect().top - WHEEL_PHYSICS.center) / WHEEL_PHYSICS.row : position.value + velocity * WHEEL_PHYSICS.projectionMs
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
/* Remaining px are the calibrated wheel row/band/viewport geometry; keep them
   aligned with WHEEL_PHYSICS, independently of the user's font scale. */
.wheel-control { display:grid; grid-template-columns:var(--es-control-min) minmax(0,1fr) var(--es-control-min); gap:var(--es-space-3); min-width:0; align-items:center; }
.wheel-step { width:var(--es-control-min); min-height:var(--es-control-min); font-size:var(--es-text-brand); border-radius:50%; }
.inertia-wheel { position: relative; height: 176px; overflow: hidden; touch-action: none; cursor: ns-resize; user-select: none; border-radius: var(--radius-sm); background: var(--surface); }
.inertia-wheel:focus-visible { outline: var(--es-focus-width) solid var(--primary); outline-offset: var(--es-focus-offset); }
.wheel-band { position: absolute; inset: 66px 12px; height: 44px; border-block: var(--es-border-width) solid var(--border-strong); background: var(--primary-soft); }
.wheel-track { position: relative; pointer-events: none; }
.wheel-track > div { height: 44px; display: flex; align-items: center; justify-content: center; gap: var(--es-space-2); color: var(--text-soft); font-size: var(--es-text-brand); font-variant-numeric: tabular-nums; }
.wheel-track > .chosen { color: var(--text); font-weight: 650; }
small { font-size: var(--es-text-label); font-weight: 400; }
</style>
