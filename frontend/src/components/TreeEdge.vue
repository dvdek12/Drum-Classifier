<template>
  <path
    :d="pathD"
    fill="none"
    stroke="#44355b"
    stroke-width="1.5"
  />
  <text
    :x="(sx + tx) / 2"
    :y="(sy + ty) / 2"
    text-anchor="middle"
    font-size="9"
    fill="#5a4878"
  >{{ isLeft ? '≤' : '>' }}</text>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sourceX: Number, sourceY: Number,
  targetX: Number, targetY: Number,
  nodeW: Number, nodeH: Number,
  isLeft: Boolean,
})

const sx = computed(() => props.sourceX + props.nodeW / 2)
const sy = computed(() => props.sourceY + props.nodeH)
const tx = computed(() => props.targetX + props.nodeW / 2)
const ty = computed(() => props.targetY)

const pathD = computed(() => {
  const my = (sy.value + ty.value) / 2
  return `M${sx.value},${sy.value} C${sx.value},${my} ${tx.value},${my} ${tx.value},${ty.value}`
})
</script>
