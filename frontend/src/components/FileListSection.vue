<template>
  <div>
    <div v-if="!state.files.length" class="empty-state">
      <div class="empty-icon">📁</div><p>brak plików</p>
    </div>
    <template v-else>
      <div class="filter-btns">
        <button
          v-for="lbl in ['all', ...Object.keys(classCounts)]" :key="lbl"
          class="filter-btn" :class="{ active: activeFilter === lbl }"
          :data-filter="lbl" @click="activeFilter = lbl"
        >
          {{ lbl === 'all' ? 'wszystkie' : lbl }}
          <span class="filter-count">{{ lbl === 'all' ? state.files.length : classCounts[lbl] }}</span>
        </button>
      </div>

      <div v-for="[label, files] in filteredGroups" :key="label" class="file-group">
        <div class="group-header" @click="toggleGroup(label)">
          <span class="file-label" :class="label">{{ label }}</span>
          <span class="group-title" :style="{ color: classColor(label) }">{{ label }}</span>
          <span class="group-count">{{ files.length }}</span>
          <span class="group-chevron" :class="{ open: !collapsedGroups[label] }">▶</span>
        </div>
        <div v-show="!collapsedGroups[label]">
          <div
            v-for="f in files" :key="f.file_id"
            class="file-item" @click="emit('preview', f.file_id)"
          >
            <span class="file-name" :title="f.filename">{{ f.filename }}</span>
            <span class="file-del" @click.stop="deleteFile(f.file_id)">✕</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from '../composables/useStore'

const emit = defineEmits(['preview'])
const { state, classCounts, deleteFile } = useStore()
const activeFilter = ref('all')
const collapsedGroups = ref({})

const CLASS_COLORS = { kick:'#e06c75', snare:'#ECA72C', hihat:'#7ec8c8', clap:'#7ecb8f', tom:'#c084fc' }
const classColor = lbl => CLASS_COLORS[lbl] || '#ECA72C'

const filteredGroups = computed(() => {
  const filtered = activeFilter.value === 'all'
    ? state.files
    : state.files.filter(f => f.label === activeFilter.value)
  const groups = {}
  filtered.forEach(f => { (groups[f.label] = groups[f.label] || []).push(f) })
  return Object.entries(groups)
})

function toggleGroup(label) {
  collapsedGroups.value[label] = !collapsedGroups.value[label]
}
</script>
