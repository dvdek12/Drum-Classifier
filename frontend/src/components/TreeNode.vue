<template>
  <g
    :transform="`translate(${x},${y})`"
    style="cursor:pointer"
    @mousemove="onHover"
    @mouseleave="$emit('tooltip', null)"
  >
    <!-- Cień -->
    <rect :width="W" :height="H" rx="8" fill="#0d0a12" transform="translate(2,3)" opacity="0.55" />

    <!-- Tło węzła -->
    <rect :width="W" :height="H" rx="8" fill="#31263e" stroke="#5a4878" stroke-width="1.5" />

    <!-- Pasek rozkładu klas (góra) -->
    <rect
      v-for="(seg, i) in distSegs" :key="i"
      :x="seg.x + 5" y="5" :width="seg.w" height="5" rx="1"
      :fill="seg.color"
    />

    <!-- Nazwa cechy -->
    <text
      :x="W / 2" y="24"
      text-anchor="middle"
      font-size="9.5"
      font-family="'Jost', monospace"
      fill="#c9a96e"
      letter-spacing="0.3"
    >{{ shortName }}</text>

    <!-- Warunek podziału: ≤ próg -->
    <text
      :x="W / 2" y="50"
      text-anchor="middle"
      font-size="15"
      font-weight="700"
      font-family="'Jost', monospace"
      fill="#f5ecd7"
    >≤ {{ fmtThresh }}</text>

    <!-- Statystyki -->
    <text
      :x="W / 2" y="68"
      text-anchor="middle"
      font-size="9"
      font-family="'Jost', monospace"
      fill="#7a6650"
    >n={{ node.samples }} · imp={{ fmtImp }}</text>

    <!-- ID węzła (prawy dolny róg) -->
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

// ─── Skrócona nazwa cechy ─────────────────────────────────────────────────────
const shortName = computed(() => {
  const n = props.node.feature_name ?? '?'
  return n
    .replace('spectral_centroid',  'sp_centroid')
    .replace('spectral_bandwidth', 'sp_bw')
    .replace('spectral_rolloff',   'sp_rolloff')
    .replace('spectral_flatness',  'sp_flat')
    .replace('zero_crossing_rate', 'zcr')
    .replace('onset_strength',     'onset')
    .replace('_mean', '_μ')
    .replace('_std',  '_σ')
})

// ─── Formatowanie liczb ───────────────────────────────────────────────────────
const fmtThresh = computed(() => {
  const v = props.node.threshold
  if (v == null) return '—'
  return Math.abs(v) < 0.001 ? v.toExponential(2) : v.toFixed(2)
})

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
  const barW  = props.W - 10   // 5px margines z każdej strony
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
      `<b>🔀 Węzeł #${props.node.node_id}</b><br>` +
      `<span style="color:#c9a96e">${props.node.feature_name}</span><br>` +
      `Próg: <b>${props.node.threshold}</b><br>` +
      `Próbki: ${props.node.samples} · Nieczystość: ${props.node.impurity?.toFixed(4) ?? '—'}<br>` +
      distHtml,
  })
}
</script>
