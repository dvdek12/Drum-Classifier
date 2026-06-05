<template>
  <g
    :transform="`translate(${x},${y})`"
    style="cursor:pointer"
    @mousemove="onHover"
    @mouseleave="$emit('tooltip', null)"
  >
    <!-- Cień -->
    <rect :width="W" :height="H" rx="8" :fill="color" transform="translate(2,3)" opacity="0.25" />

    <!-- Tło liścia (kolorowane klasą) -->
    <rect :width="W" :height="H" rx="8" :fill="colorBg" :stroke="color" stroke-width="2" />

    <!-- Pasek rozkładu klas (góra) -->
    <rect
      v-for="(seg, i) in distSegs" :key="i"
      :x="seg.x + 5" y="5" :width="seg.w" height="5" rx="1"
      :fill="seg.color"
    />

    <!-- Etykieta roli -->
    <text
      :x="W / 2" y="26"
      text-anchor="middle"
      font-size="8.5"
      font-family="'Jost', monospace"
      fill="#7a6650"
      letter-spacing="1.5"
    >PROGNOZA</text>

    <!-- Nazwa klasy (prominentnie) -->
    <text
      :x="W / 2" y="56"
      text-anchor="middle"
      font-size="20"
      font-weight="700"
      font-family="'Jost', monospace"
      :fill="color"
      letter-spacing="0.5"
    >{{ (node.predicted_class ?? '').toUpperCase() }}</text>

    <!-- Statystyki -->
    <text
      :x="W / 2" y="74"
      text-anchor="middle"
      font-size="9"
      font-family="'Jost', monospace"
      fill="#7a6650"
    >n={{ node.samples }} · imp={{ fmtImp }}</text>

    <!-- ID węzła -->
    <text
      :x="W - 7" :y="H - 6"
      text-anchor="end"
      font-size="8"
      font-family="'Jost', monospace"
      fill="#44355b"
    >#{{ node.node_id }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue'

// ─── Props / emits ────────────────────────────────────────────────────────────
const props = defineProps({
  node: Object,
  x:    Number,
  y:    Number,
  W:    Number,
  H:    Number,
})
const emit = defineEmits(['tooltip'])

// ─── Kolory klas ──────────────────────────────────────────────────────────────
const CLASS_COLORS = {
  kick:  '#e06c75',
  snare: '#ECA72C',
  hihat: '#7ec8c8',
  clap:  '#7ecb8f',
  tom:   '#c084fc',
}
const fallback = '#ECA72C'

const color    = computed(() => CLASS_COLORS[props.node.predicted_class] ?? fallback)
const colorBg  = computed(() => color.value + '22')   // 13% opacity jako tło

const fmtImp = computed(() => {
  const v = props.node.impurity
  if (v == null) return '—'
  return Math.abs(v) < 0.0001 ? '0' : v.toFixed(3)
})

// ─── Segmenty paska rozkładu ──────────────────────────────────────────────────
const distSegs = computed(() => {
  const dist  = props.node.class_distribution ?? {}
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  if (!total) return []
  const barW  = props.W - 10
  let xOff = 0
  return Object.entries(dist).map(([cls, cnt]) => {
    const w   = (cnt / total) * barW
    const seg = { x: xOff, w: Math.max(w, 1), color: CLASS_COLORS[cls] ?? fallback }
    xOff += w
    return seg
  })
})

// ─── Tooltip ──────────────────────────────────────────────────────────────────
function onHover(e) {
  const distHtml = Object.entries(props.node.class_distribution ?? {})
    .map(([k, v]) => `<span style="color:${CLASS_COLORS[k] ?? fallback}">${k}: ${v}</span>`)
    .join(' · ')

  emit('tooltip', {
    event: e,
    html:
      `<b>🍃 Liść #${props.node.node_id}</b><br>` +
      `Klasa: <b style="color:${color.value}">${props.node.predicted_class}</b><br>` +
      `Próbki: ${props.node.samples} · Nieczystość: ${props.node.impurity?.toFixed(4) ?? '—'}<br>` +
      distHtml,
  })
}
</script>
