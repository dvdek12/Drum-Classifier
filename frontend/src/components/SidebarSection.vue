<template>
  <div class="section" :class="{ collapsed }">
    <div class="section-header" @click="collapsed = !collapsed">
      <span class="section-num">{{ num }}</span>
      <h3><slot name="title" /></h3>
      <span class="sec-chevron">▾</span>
    </div>
    <div class="section-body">
      <div class="section-inner">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
defineProps({ num: String })
const collapsed = ref(false)
</script>
