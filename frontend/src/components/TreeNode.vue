<template>
  <g
    class="tree-node"
    :transform="`translate(${x},${y})`"
    @mousemove="onHover"
    @mouseleave="$emit('tooltip', null)"
  >
    <rect
      :width="W" :height="H" rx="6"
      fill="#31263e"
      stroke="#44355b"
      stroke-width="1"
    />
    <text :x="W/2" y="18" text-anchor="middle" font-size="10" fill="#c9a96e">
      {{ shortName }}
    </text>
    <text :x="W/2" y="34" text-anchor="middle" font-size="12" font-weight="700" fill="#f5ecd7">
      ≤ {{ node.threshold }}
    </text>
    <text :x="W/2" y="50" text-anchor="middle" font-size="9" fill="#7a6650">
      n={{ node.samples }} · imp={{ node.impurity }}
    </text>
  </g>
</template>

<script setup>
const props = defineProps({
  node: Object,
  x: Number, y: Number,
  W: Number, H: Number,
})
const emit = defineEmits(['tooltip'])

const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }

const shortName = computed(() =>
  props.node.feature_name
    .replace('spectral_', 'sp_')
    .replace('_mean', '_μ')
    .replace('_std', '_σ')
)

function onHover(e) {
  emit('tooltip', {
    event: e,
    html: `<b>🔀 Węzeł</b><br>Cecha: ${props.node.feature_name}<br>Próg: ${props.node.threshold}<br>` +
      `Próbki: ${props.node.samples}<br>Nieczystość: ${props.node.impurity}<br>` +
      Object.entries(props.node.class_distribution || {})
        .map(([k,v]) => `<span style="color:${CLASS_COLORS[k]||'#ECA72C'}">${k}: ${v}</span>`).join(' · ')
  })
}

import { computed } from 'vue'
</script>
