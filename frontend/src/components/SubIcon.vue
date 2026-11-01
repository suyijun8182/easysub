<template>
  <span class="sub-icon" :style="{ '--sz': size + 'px' }" aria-hidden="true">
    <img v-if="isImg(icon)" :src="icon" alt="" loading="lazy" @error="broken = true" v-show="!broken" />
    <span v-if="!isImg(icon) && icon" class="glyph">{{ icon }}</span>
    <span v-else-if="!isImg(icon) || broken" class="initial">{{ initial }}</span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { isImg } from '../lifeline'

// 订阅图标：上传/图库图片、用户填的 emoji，或取名称首字作为占位
const props = defineProps({ icon: String, name: String, size: { type: Number, default: 40 } })
const broken = ref(false)
watch(() => props.icon, () => { broken.value = false })
const initial = computed(() => (props.name || '?').trim().charAt(0).toUpperCase())
</script>

<style scoped>
.sub-icon { width: var(--sz); height: var(--sz); flex-shrink: 0; display: inline-flex; align-items: center;
  justify-content: center; border-radius: calc(var(--sz) * .26); background: var(--surface);
  border: 1px solid var(--border); overflow: hidden; }
img { width: 76%; height: 76%; object-fit: contain; }
.glyph { font-size: calc(var(--sz) * .55); line-height: 1; }
.initial { font-size: calc(var(--sz) * .42); font-weight: 650; color: var(--text-soft); }
</style>
