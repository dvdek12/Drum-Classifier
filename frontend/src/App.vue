<template>
  <div class="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">

    <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
      {{ sidebarCollapsed ? '❯' : '❮' }}
    </button>

    <header class="topbar">
      <div class="topbar-logo">DRUM<span>/</span>CLASSIFIER</div>
    </header>

    <aside class="sidebar">
      <SidebarSection num="01">
        <template #title>Presety</template>
        <PresetLoader />
      </SidebarSection>

      <SidebarSection num="02" :collapsed-default="true">
        <template #title>Wgraj ręcznie</template>
        <UploadSection />
      </SidebarSection>

      <SidebarSection num="03">
        <template #title>Pliki <span style="color:var(--text3);font-size:10px">({{ state.files.length }})</span></template>
        <FileListSection @preview="onPreview" />
      </SidebarSection>

      <SidebarSection num="04">
        <template #title>Parametry</template>
        <ParamsSection ref="paramsRef" />
      </SidebarSection>

      <SidebarSection num="05">
        <template #title>Akcje</template>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button class="btn btn-primary" :disabled="!readyToTrain || training" @click="onTrain">
            <span v-if="training" class="spinner"></span>
            {{ training ? 'trenowanie...' : '▶ Trenuj drzewo' }}
          </button>
          <button class="btn btn-outline" :disabled="!state.trainedModel" @click="exportResults">
            ↓ Eksportuj wyniki JSON
          </button>
        </div>
      </SidebarSection>
    </aside>

    <main class="main">
      <div class="tabs">
        <div v-for="tab in tabs" :key="tab.id" class="tab" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
          {{ tab.label }}
        </div>
      </div>

      <div class="panel" :class="{ active: activeTab === 'waveform' }">
        <WaveformPanel :file-info="previewFile" :wave-data="waveData" />
      </div>
      <div class="panel tree-panel-wrap" :class="{ active: activeTab === 'tree' }" id="panel-tree">
        <TreePanel :tree-data="state.trainedModel" :visible="activeTab === 'tree'" :training="training" />
      </div>
      <div class="panel" :class="{ active: activeTab === 'metrics' }">
        <MetricsPanel :evaluation="state.trainedModel?.evaluation" />
      </div>
      <div class="panel" :class="{ active: activeTab === 'predict' }">
        <PredictPanel />
      </div>
    </main>
  </div>

  <div
    v-for="(t, i) in state.toasts" :key="t.id"
    class="toast show" :class="t.type"
    :style="{ bottom: (24 + i * 60) + 'px' }"
  >{{ t.msg }}</div>
</template>

<script setup>
import { ref } from 'vue'
import { useStore } from './composables/useStore'
import SidebarSection from './components/SidebarSection.vue'
import PresetLoader from './components/PresetLoader.vue'
import UploadSection from './components/UploadSection.vue'
import FileListSection from './components/FileListSection.vue'
import ParamsSection from './components/ParamsSection.vue'
import TreePanel from './components/TreePanel.vue'
import WaveformPanel from './components/WaveformPanel.vue'
import MetricsPanel from './components/MetricsPanel.vue'
import PredictPanel from './components/PredictPanel.vue'

const { state, readyToTrain, trainModel, exportResults, toast } = useStore()

const sidebarCollapsed = ref(false)
const activeTab = ref('waveform')
const training = ref(false)
const paramsRef = ref(null)
const previewFile = ref(null)
const waveData = ref(null)

const tabs = [
  { id: 'waveform', label: 'Wizualizacja danych' },
  { id: 'tree',     label: 'Drzewo decyzyjne' },
  { id: 'metrics',  label: 'Ocena modelu' },
  { id: 'predict',  label: 'Predykcja' },
]

async function onTrain() {
  training.value = true
  activeTab.value = 'tree'   // pokaż animację od razu
  try {
    const p = paramsRef.value.params
    await trainModel({ ...p, test_split: p.test_split_pct / 100 })
  } catch (e) {
    toast('Błąd: ' + e.message, 'err')
  } finally {
    training.value = false
  }
}

async function onPreview(fileId) {
  activeTab.value = 'waveform'
  let file = state.files.find(f => f.file_id === fileId)
  if (!file) return

  // Pliki z presetu mają tylko minimalne dane — pobierz pełne (z cechami)
  if (!file.features) {
    const r = await fetch(`/files/${fileId}`)
    if (r.ok) {
      const full = await r.json()
      Object.assign(file, full)
    }
  }

  previewFile.value = file
  const r = await fetch(`/files/${fileId}/waveform`)
  waveData.value = await r.json()
}
</script>
