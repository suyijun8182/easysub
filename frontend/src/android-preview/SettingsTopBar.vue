<script setup>
import {useI18n} from 'vue-i18n'
import {icon} from '../icons.js'
defineProps({title:{type:String,required:true}})
const {t}=useI18n()
</script>
<template>
  <header class="app-subpage-bar"><router-link to="/settings" class="app-settings-back" :aria-label="t('mobile.back')"><span aria-hidden="true" v-html="icon('chevronL')"></span></router-link><h1>{{ title }}</h1></header>
</template>
<style scoped>
.app-subpage-bar { display:flex; align-items:center; gap:var(--es-space-2); min-height:calc(var(--es-control-min) + var(--es-space-4)); margin-bottom:var(--es-space-4); border-bottom:var(--es-border-width) solid var(--border); background:var(--bg); }
.app-settings-back { display:grid; place-items:center; flex:none; width:var(--es-control-min); height:var(--es-control-min); border-radius:var(--es-radius-round); color:var(--text); }
.app-settings-back span { display:block; width:var(--es-icon-nav); height:var(--es-icon-nav); }
.app-subpage-bar h1 { font-size:var(--es-text-section); margin:0; }
</style>
