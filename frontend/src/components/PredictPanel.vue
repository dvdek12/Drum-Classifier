<template>
  <div style="max-width:520px">
    <p style="font-size:13px;color:var(--text2);margin-bottom:16px">Wgraj nowy plik audio — klasyfikator powie co to za instrument.</p>
    <div class="upload-zone" @click="input.click()" style="margin-bottom:0">
      <input ref="input" type="file" accept=".wav,.mp3,.flac,.ogg,.aiff" style="display:none" @change="onFile" />
      <div class="upload-icon">🔍</div>
      <strong>Wgraj sample do klasyfikacji</strong>
      <p>wynik pojawi się poniżej</p>
    </div>
    <div v-if="loading" style="padding:20px;font-family:var(--mono);font-size:13px;color:var(--text2);text-align:center">
      <span class="spinner"></span> Klasyfikuję...
    </div>
    <div v-if="result" class="predict-result">
      <div class="predict-class" :style="{ color: classColor(result.predicted_class) }">{{ result.predicted_class.toUpperCase() }}</div>
      <div class="predict-file">{{ result.filename }} · {{ result.waveform?.duration_sec }}s</div>
      <div style="max-width:320px;margin:0 auto">
        <div v-for="[cls, prob] in sortedProbs" :key="cls" class="prob-row">
          <span class="prob-name" :style="{ color: classColor(cls) }">{{ cls }}</span>
          <div class="prob-bar-wrap"><div class="prob-bar" :style="{ width: (prob*100).toFixed(0)+'%', background: classColor(cls) }"></div></div>
          <span class="prob-val">{{ (prob*100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from '../composables/useStore'

const { state, predict, toast } = useStore()
const input = ref(null)
const loading = ref(false)
const result = ref(null)
const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }
const classColor = cls => CLASS_COLORS[cls] || '#ECA72C'
const sortedProbs = computed(() => Object.entries(result.value?.probabilities || {}).sort((a,b) => b[1]-a[1]))

async function onFile(e) {
  const file = e.target.files[0]; if (!file) return
  if (!state.trainedModel) { toast('Najpierw wytrenuj drzewo!', 'err'); return }
  loading.value = true; result.value = null
  try { result.value = await predict(file) }
  catch (err) { toast('Błąd predykcji: ' + err.message, 'err') }
  finally { loading.value = false; e.target.value = '' }
}
</script>
