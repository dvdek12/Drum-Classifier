<template>
  <div>
    <div class="param-row">
      <label>Kryterium podziału</label>
      <select v-model="params.criterion">
        <option value="gini">Gini impurity</option>
        <option value="entropy">Entropia informacyjna</option>
      </select>
    </div>
    <div class="param-row">
      <label>Maks. głębokość <span>{{ params.max_depth }}</span></label>
      <input type="range" min="1" max="15" v-model.number="params.max_depth" />
    </div>
    <div class="param-row">
      <label>Min. próbek do podziału <span>{{ params.min_samples_split }}</span></label>
      <input type="range" min="2" max="20" v-model.number="params.min_samples_split" />
    </div>
    <div class="param-row">
      <label>Min. próbek w liściu <span>{{ params.min_samples_leaf }}</span></label>
      <input type="range" min="1" max="10" v-model.number="params.min_samples_leaf" />
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
  min_samples_split: 2,
  min_samples_leaf: 1,
  test_split_pct: 20,
})

defineExpose({ params })
</script>
