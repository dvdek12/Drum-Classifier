<template>
  <div class="pl-root">

    <!-- Folder hint gdy brak presetów -->
    <div v-if="!presets.length && !loading" class="pl-empty">
      <div class="pl-empty-icon">📁</div>
      <p class="pl-empty-title">Brak presetów</p>
      <p class="pl-empty-sub">
        Utwórz podfoldery w <code>presets/</code>:
      </p>
      <pre class="pl-tree">presets/
  maly_40/
    kick/   ← *.wav
    snare/
    hihat/
    clap/
    tom/
  duzy_500/
    kick/
    ...</pre>
    </div>

    <!-- Lista presetów -->
    <div v-for="p in presets" :key="p.name" class="pl-preset"
      :class="{ 'pl-preset--active': activePreset === p.name }">

      <!-- Wiersz 1: nazwa + liczba + przycisk -->
      <div class="pl-row">
        <div class="pl-meta">
          <span class="pl-preset-name">{{ p.name }}</span>
          <span class="pl-preset-total">{{ p.total }} plików</span>
        </div>
        <button
          class="pl-load-btn"
          :disabled="jobRunning"
          @click="loadPreset(p.name)"
        >
          <span v-if="jobRunning && job.preset === p.name" class="spinner" />
          {{ jobRunning && job.preset === p.name ? 'Wczytywanie…' : 'Wczytaj' }}
        </button>
      </div>

      <!-- Wiersz 2: chipy klas -->
      <div class="pl-classes">
        <span v-for="(cnt, cls) in p.classes" :key="cls"
          class="pl-cls-chip" :class="cls">
          {{ cls }}&nbsp;<b>{{ cnt }}</b>
        </span>
      </div>

      <!-- Wiersz 3: pasek postępu -->
      <template v-if="jobRunning && job.preset === p.name">
        <div class="pl-progress-bar">
          <div class="pl-progress-fill" :style="{ width: progressPct + '%' }" />
        </div>
        <div class="pl-progress-label">{{ job.done }} / {{ job.total }}</div>
      </template>

    </div>

    <!-- Komunikat po zakończeniu -->
    <Transition name="pl-done-fade">
      <div v-if="doneMsg" class="pl-done">
        ✓ {{ doneMsg }}
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useStore } from '../composables/useStore'

const { state, toast, refreshFiles } = useStore()

// ── Stan ──────────────────────────────────────────────────────────────────────
const presets  = ref([])
const loading  = ref(false)
const job      = ref({ phase: 'idle', preset: '', total: 0, done: 0, errors: 0 })
const doneMsg  = ref('')
let pollTimer  = null
let doneTimer  = null

// ── Computed ──────────────────────────────────────────────────────────────────
const jobRunning   = computed(() => job.value.phase === 'running')
const activePreset = computed(() => job.value.phase === 'done' ? job.value.preset : '')
const progressPct  = computed(() =>
  job.value.total ? Math.round((job.value.done / job.value.total) * 100) : 0
)

// ── Fetch presetów ────────────────────────────────────────────────────────────
async function fetchPresets() {
  loading.value = true
  try {
    const r = await fetch('/presets')
    const d = await r.json()
    presets.value = d.presets ?? []
  } finally {
    loading.value = false
  }
}

// ── Ładowanie presetu ─────────────────────────────────────────────────────────
async function loadPreset(name) {
  job.value = { phase: 'running', preset: name, total: 0, done: 0, errors: 0 }
  doneMsg.value = ''

  const r = await fetch(`/presets/${encodeURIComponent(name)}/load`, { method: 'POST' })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    toast('Błąd: ' + (err.detail ?? 'nieznany'), 'err')
    job.value.phase = 'idle'
    return
  }

  // Polling postępu
  pollTimer = setInterval(async () => {
    try {
      const pr = await fetch(`/presets/${encodeURIComponent(name)}/progress`)
      const pd = await pr.json()
      job.value = pd

      if (pd.phase === 'done') {
        clearInterval(pollTimer)
        pollTimer = null
        await refreshFiles()
        await fetchPresets()

        doneMsg.value = `Wczytano ${pd.done} plików${pd.errors ? `, ${pd.errors} błędów` : ''}`
        doneTimer = setTimeout(() => { doneMsg.value = '' }, 4000)

        if (pd.errors > 0) toast(`${pd.errors} plików nie udało się wczytać`, 'err')
        else toast(`Preset "${name}" załadowany (${pd.done} plików)`)
      }
    } catch {
      // sieć — spróbuj znowu za chwilę
    }
  }, 300)
}

onUnmounted(() => {
  clearInterval(pollTimer)
  clearTimeout(doneTimer)
})

fetchPresets()
</script>

<style scoped>
.pl-root { display: flex; flex-direction: column; gap: 10px; }

/* ── Pusty stan ─────────────────────────────────────────────────────────────── */
.pl-empty {
  background: var(--bg3);
  border: 1px dashed var(--border2);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.pl-empty-icon { font-size: 22px; margin-bottom: 6px; }
.pl-empty-title { font-family: var(--mono); font-size: 12px; color: var(--text2); margin-bottom: 4px; font-weight: 700; }
.pl-empty-sub { font-size: 11px; color: var(--text3); margin-bottom: 8px; }
.pl-tree {
  text-align: left;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text2);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  line-height: 1.6;
  display: inline-block;
  width: 100%;
  box-sizing: border-box;
}
code {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent);
  background: rgba(236,167,44,.1);
  padding: 1px 5px;
  border-radius: 3px;
}

/* ── Preset card ────────────────────────────────────────────────────────────── */
.pl-preset {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color .15s;
}
.pl-preset--active { border-color: var(--accent); }

/* Wiersz: nazwa + przycisk */
.pl-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pl-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  overflow: hidden;
}
.pl-preset-name {
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 700;
  color: var(--accent);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pl-preset-total {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  flex-shrink: 0;
}

.pl-load-btn {
  flex-shrink: 0;
  padding: 5px 14px;
  font-size: 12px;
  background: var(--accent);
  color: #221E22;
  border-radius: 6px;
  border: none;
  font-family: var(--mono);
  font-weight: 700;
  cursor: pointer;
  transition: background .15s;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.pl-load-btn:hover:not(:disabled) { background: var(--accent2); }
.pl-load-btn:disabled { background: var(--bg3); color: var(--text3); cursor: not-allowed; }

/* ── Klasy ──────────────────────────────────────────────────────────────────── */
.pl-classes { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 4px; }
.pl-cls-chip {
  font-family: var(--mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid;
  font-weight: 600;
}
.pl-cls-chip.kick  { color: var(--kick);  border-color: var(--kick);  background: rgba(224,108,117,.1); }
.pl-cls-chip.snare { color: var(--snare); border-color: var(--snare); background: rgba(236,167,44,.1); }
.pl-cls-chip.hihat { color: var(--hihat); border-color: var(--hihat); background: rgba(126,200,200,.1); }
.pl-cls-chip.clap  { color: var(--clap);  border-color: var(--clap);  background: rgba(126,203,143,.1); }
.pl-cls-chip.tom   { color: var(--tom);   border-color: var(--tom);   background: rgba(192,132,252,.1); }
/* nieznane klasy */
.pl-cls-chip:not(.kick):not(.snare):not(.hihat):not(.clap):not(.tom) {
  color: var(--text2); border-color: var(--border2); background: transparent;
}

/* ── Pasek postępu ──────────────────────────────────────────────────────────── */
.pl-progress-bar {
  height: 5px;
  background: var(--bg3);
  border-radius: 3px;
  margin-top: 8px;
  overflow: hidden;
}
.pl-progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width .25s ease;
}
.pl-progress-label {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text3);
  margin-top: 4px;
}

/* ── Done msg ───────────────────────────────────────────────────────────────── */
.pl-done {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--green);
  background: rgba(126,203,143,.08);
  border: 1px solid rgba(126,203,143,.25);
  border-radius: 6px;
  padding: 6px 10px;
}
.pl-done-fade-enter-active, .pl-done-fade-leave-active { transition: opacity .3s; }
.pl-done-fade-enter-from, .pl-done-fade-leave-to { opacity: 0; }
</style>
