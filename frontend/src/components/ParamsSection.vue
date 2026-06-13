<template>
  <div>
    <div class="param-row">
      <label>Kryterium podziału</label>
      <select v-model="params.criterion">
        <option value="gini">Gini impurity</option>
        <option value="information_gain">Information Gain</option>
        <option value="gain_ratio">Gain Ratio</option>
      </select>
    </div>
    <div class="param-row">
      <label>Maks. głębokość <span>{{ params.max_depth }}</span></label>
      <input type="range" min="1" max="15" v-model.number="params.max_depth" />
    </div>
    <div class="param-row">
      <label>Min. example count <span>{{ params.min_example_count }}</span></label>
      <input type="range" min="1" max="20" v-model.number="params.min_example_count" />
    </div>
    <div class="param-row">
      <label>Min. information gain <span>{{ params.min_gain.toFixed(2) }}</span></label>
      <input type="range" min="0" max="0.5" step="0.01" v-model.number="params.min_gain" />
    </div>
    <div class="param-row">
      <label>Test split <span>{{ params.test_split_pct }}%</span></label>
      <input type="range" min="10" max="40" v-model.number="params.test_split_pct" />
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const params = reactive({
  criterion: 'gini',
  max_depth: 5,
  min_example_count: 2,
  min_gain: 0.0,
  test_split_pct: 20,
})

defineExpose({ params })
</script>
