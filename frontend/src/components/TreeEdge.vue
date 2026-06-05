<template>
  <g>
    <!-- Krzywa Béziera łącząca węzeł-rodzic z węzłem-dzieckiem -->
    <path
      :d="pathD"
      fill="none"
      :stroke="edgeColor"
      stroke-width="2"
      stroke-linecap="round"
      opacity="0.65"
    />
    <!-- Etykieta warunku (≤ / >) -->
    <text
      :x="labelX"
      :y="labelY"
      text-anchor="middle"
      font-size="11"
      font-weight="700"
      font-family="'Jost', monospace"
      :fill="labelColor"
    >{{ isLeft ? '≤' : '>' }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue'

// ─── Props ────────────────────────────────────────────────────────────────────
const props = defineProps({
  sourceX: Number,   // _px lewego górnego rogu rodzica
  sourceY: Number,   // _py lewego górnego rogu rodzica
  targetX: Number,
  targetY: Number,
  nodeW:   Number,
  nodeH:   Number,
  isLeft:  Boolean,  // true → gałąź lewa (≤), false → prawa (>)
})

// ─── Punkty kotwiczące ────────────────────────────────────────────────────────
// Wychodzą ze środka dolnej krawędzi rodzica, wchodzą w środek górnej krawędzi dziecka
const sx = computed(() => props.sourceX + props.nodeW / 2)
const sy = computed(() => props.sourceY + props.nodeH)
const tx = computed(() => props.targetX + props.nodeW / 2)
const ty = computed(() => props.targetY)

// ─── Krzywa kubiczna Béziera ──────────────────────────────────────────────────
const my = computed(() => (sy.value + ty.value) / 2)
const pathD = computed(() =>
  `M${sx.value},${sy.value} C${sx.value},${my.value} ${tx.value},${my.value} ${tx.value},${ty.value}`
)

// ─── Kolory ───────────────────────────────────────────────────────────────────
const edgeColor  = computed(() => props.isLeft ? '#4a7a5a' : '#7a4a55')
const labelColor = computed(() => props.isLeft ? '#7ecb8f' : '#e06c75')

// ─── Pozycja etykiety (1/3 długości krzywej, przesunięta w bok) ───────────────
const labelX = computed(() => sx.value + (tx.value - sx.value) * 0.28)
const labelY = computed(() => sy.value + (ty.value - sy.value) * 0.28 - 4)
</script>
