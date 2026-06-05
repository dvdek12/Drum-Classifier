<template>
  <g
    class="tree-node"
    :transform="`translate(${x},${y})`"
    @mousemove="onHover"
    @mouseleave="$emit('tooltip', null)"
  >
    <rect
      :width="W" :height="H" rx="6"
      :fill="color + '22'"
      :stroke="color"
      stroke-width="1.5"
    />
    <text :x="W/2" y="20" text-anchor="middle" font-size="11" font-weight="700" :fill="color">
      {{ node.predicted_class.toUpperCase() }}
    </text>
    <text :x="W/2" y="36" text-anchor="middle" font-size="9" fill="#7a6650">
      n={{ node.samples }} · imp={{ node.impurity }}
    </text>
    <text :x="W/2" y="50" text-anchor="middle" font-size="8" fill="#44355b">
      {{ distText }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  node: Object,
  x: Number, y: Number,
  W: Number, H: Number,
})
const emit = defineEmits(['tooltip'])

const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }
const color = computed(() => CLASS_COLORS[props.node.predicted_class] || '#ECA72C')
const distText = computed(() =>
  Object.entries(props.node.class_distribution || {}).map(([k,v]) => `${k}:${v}`).join(' ')
)

function onHover(e) {
  emit('tooltip', {
    event: e,
    html: `<b>🍃 Liść</b><br>Klasa: <b style="color:${color.value}">${props.node.predicted_class}</b><br>` +
      `Próbki: ${props.node.samples}<br>Nieczystość: ${props.node.impurity}<br>` +
      Object.entries(props.node.class_distribution || {})
        .map(([k,v]) => `<span style="color:${CLASS_COLORS[k]||'#ECA72C'}">${k}: ${v}</span>`).join(' · ')
  })
}
</script>
