<template>
  <div v-if="!evaluation" class="empty-state" style="padding:80px 0">
    <div class="empty-icon">📊</div><p>wytrenuj drzewo żeby zobaczyć metryki</p>
  </div>
  <div v-else>
    <div class="metrics-grid">
      <div class="metric-card good"><div class="metric-val">{{ q.accuracy_pct.toFixed(1) }}%</div><div class="metric-label">Accuracy (test)</div></div>
      <div class="metric-card amber"><div class="metric-val">{{ (evaluation.train_accuracy * 100).toFixed(1) }}%</div><div class="metric-label">Accuracy (train)</div></div>
      <div class="metric-card info"><div class="metric-val">{{ e.tree_nodes_total }}</div><div class="metric-label">Węzłów</div></div>
      <div class="metric-card cyan"><div class="metric-val">{{ e.tree_actual_depth }}</div><div class="metric-label">Głębokość</div></div>
    </div>

    <div class="cm-wrap">
      <div class="cm-title">Macierz konfuzji · wiersze = prawdziwe · kolumny = przewidywane</div>
      <table class="cm-table">
        <thead><tr><th></th><th v-for="c in classes" :key="c" :style="{ color: classColor(c) }">{{ c }}</th></tr></thead>
        <tbody>
          <tr v-for="(row, i) in matrix" :key="i">
            <th :style="{ color: classColor(classes[i]) }">{{ classes[i] }}</th>
            <td v-for="(v, j) in row" :key="j" :class="{ diag: i===j, off: i!==j && v>0 }">{{ v }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="per-class">
      <div class="per-class-title">F1-score per klasa</div>
      <div v-for="cls in classes" :key="cls" class="cls-row">
        <span class="cls-name" :style="{ color: classColor(cls) }">{{ cls }}</span>
        <div class="cls-bar-wrap"><div class="cls-bar" :style="{ width: ((perClass[cls]?.f1||0)*100)+'%', background: classColor(cls) }"></div></div>
        <span class="cls-f1">F1: {{ ((perClass[cls]?.f1||0)*100).toFixed(0) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ evaluation: Object })
const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }
const classColor = cls => CLASS_COLORS[cls] || '#ECA72C'
const q = computed(() => props.evaluation?.quality)
const e = computed(() => props.evaluation?.efficiency)
const classes = computed(() => q.value?.confusion_matrix?.labels || [])
const matrix = computed(() => q.value?.confusion_matrix?.matrix || [])
const perClass = computed(() => q.value?.per_class || {})
</script>
