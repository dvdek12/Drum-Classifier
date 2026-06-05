<template>
  <div v-if="!fileInfo" class="empty-state" style="padding:80px 0">
    <div class="empty-icon">🎚️</div><p>wgraj sample żeby zobaczyć dane</p>
  </div>
  <div v-else>
    <div style="margin-bottom:8px;display:flex;align-items:center;gap:10px;">
      <span class="file-label" :class="fileInfo.label">{{ fileInfo.label }}</span>
      <span style="font-family:var(--mono);font-size:13px;color:var(--text)">{{ fileInfo.filename }}</span>
      <span style="font-size:11px;color:var(--text3);font-family:var(--mono);margin-left:auto">{{ waveData?.duration_sec }}s · {{ waveData?.sample_rate }}Hz · {{ fileInfo.n_features }} cech</span>
    </div>
    <div class="wave-container">
      <div class="wave-title">Fala dźwiękowa</div>
      <canvas ref="canvas" height="80"></canvas>
    </div>
    <div style="font-family:var(--mono);font-size:11px;color:var(--text2);margin-bottom:12px;text-transform:uppercase;letter-spacing:1px">
      Wektor cech ({{ features.length }} wartości)
    </div>
    <div class="feat-grid">
      <div v-for="(name, i) in featureNames" :key="name" class="feat-card">
        <div class="feat-name" :title="name">{{ name }}</div>
        <div class="feat-bar-wrap"><div class="feat-bar" :style="{ width: pct(i) + '%', background: classColor(fileInfo.label) }"></div></div>
        <div class="feat-val">{{ (features[i] || 0).toFixed(4) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({ fileInfo: Object, waveData: Object })
const canvas = ref(null)
const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }
const classColor = cls => CLASS_COLORS[cls] || '#ECA72C'

const features = computed(() => props.fileInfo?.features || [])
const featureNames = computed(() => props.fileInfo?.feature_names || [])
const maxAbs = computed(() => Math.max(...features.value.map(Math.abs), 1e-6))
const pct = i => Math.min(100, Math.abs(features.value[i] || 0) / maxAbs.value * 100)

watch(() => props.waveData, async () => {
  await nextTick()
  if (canvas.value && props.waveData) drawWaveform()
})

function drawWaveform() {
  const c = canvas.value
  const color = classColor(props.fileInfo.label)
  c.width = c.offsetWidth * window.devicePixelRatio
  c.height = 80 * window.devicePixelRatio
  const ctx = c.getContext('2d')
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
  const W = c.offsetWidth, H = 80, mid = H / 2
  ctx.clearRect(0, 0, W, H)
  ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.beginPath()
  const samples = props.waveData.waveform
  samples.forEach((v, i) => {
    const x = (i / samples.length) * W, y = mid - v * (mid - 4)
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.stroke()
  ctx.lineTo(W, mid); ctx.lineTo(0, mid); ctx.closePath()
  ctx.fillStyle = color + '22'; ctx.fill()
}
</script>
