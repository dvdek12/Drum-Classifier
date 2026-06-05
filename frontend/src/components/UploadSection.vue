<template>
  <div>
    <div class="label-select">
      <button
        v-for="lbl in labels" :key="lbl"
        class="label-btn" :class="{ active: selectedLabel === lbl }"
        :data-label="lbl" @click="selectedLabel = lbl"
      >{{ lbl }}</button>
    </div>

    <div class="upload-zone" :class="{ drag: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput.click()"
    >
      <input ref="fileInput" type="file" accept=".wav,.mp3,.flac,.ogg,.aiff" multiple style="display:none" @change="onFileChange" />
      <div class="upload-icon">🎵</div>
      <strong>Przeciągnij pliki audio</strong>
      <p>lub kliknij · WAV / MP3 / FLAC</p>
    </div>

    <div v-if="uploading" class="upload-progress">
      <span class="spinner"></span> Przetwarzanie {{ pendingCount }} plik(ów)...
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useStore } from '../composables/useStore'

const { uploadBatch } = useStore()
const labels = ['kick', 'snare', 'hihat', 'clap', 'tom']
const selectedLabel = ref('kick')
const isDragging = ref(false)
const uploading = ref(false)
const pendingCount = ref(0)
const fileInput = ref(null)

async function handleFiles(files) {
  if (!files.length) return
  uploading.value = true
  pendingCount.value = files.length
  try {
    await uploadBatch(files, selectedLabel.value)
  } finally {
    uploading.value = false
  }
}

function onFileChange(e) {
  handleFiles([...e.target.files])
  e.target.value = ''
}

function onDrop(e) {
  isDragging.value = false
  const files = [...e.dataTransfer.files].filter(f => /\.(wav|mp3|flac|ogg|aiff)$/i.test(f.name))
  handleFiles(files)
}
</script>
