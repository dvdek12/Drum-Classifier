<template>
  <div v-if="!fileInfo" class="empty-state" style="padding:80px 0">
    <div class="empty-icon">🎚️</div>
    <p>Wgraj sample żeby zobaczyć dane</p>
  </div>

  <div v-else class="wp-root">

    <!-- ── Nagłówek pliku ──────────────────────────────────────────── -->
    <div class="wp-file-header">
      <span class="file-label" :class="fileInfo.label">{{ fileInfo.label }}</span>
      <span class="wp-filename">{{ fileInfo.filename }}</span>
      <span class="wp-meta">
        {{ waveData?.duration_sec }}s · {{ waveData?.sample_rate }} Hz · {{ features.length }} cech
      </span>
    </div>

    <!-- ── Fala dźwiękowa ─────────────────────────────────────────── -->
    <div class="wave-container">
      <div class="wave-title">Fala dźwiękowa</div>
      <canvas ref="canvas" height="80" />
    </div>

    <!-- ── Karty cech ────────────────────────────────────────────── -->
    <div class="feat-grid">
      <div
        v-for="(name, idx) in featureNames" :key="name"
        class="feat-card"
        :class="{ 'feat-card--hovered': hovered === name }"
        @mouseenter="hovered = name"
        @mouseleave="hovered = null"
      >
        <div class="feat-card-top">
          <span class="feat-friendly">{{ FEAT_DESC[name]?.short ?? name }}</span>
          <span class="feat-raw">{{ name }}</span>
        </div>
        <div class="feat-bar-wrap">
          <div class="feat-bar"
            :style="{ width: pct(idx) + '%', background: classColor(fileInfo.label) }" />
        </div>
        <div class="feat-val">{{ fmtVal(features[idx]) }}</div>
      </div>
    </div>

    <!-- ── Tooltip ────────────────────────────────────────────────── -->
    <Transition name="tt-fade">
      <div v-if="hoveredDesc" class="feat-tooltip" :style="ttStyle">
        <div class="tt-title">{{ hoveredDesc.short }}</div>
        <div class="tt-body">{{ hoveredDesc.detail }}</div>
        <div class="tt-drum" v-if="hoveredDesc.drums">
          <span v-for="(val, drum) in hoveredDesc.drums" :key="drum"
            class="tt-drum-chip" :class="drum">
            {{ drum }}: {{ val }}
          </span>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, watch, reactive, nextTick } from 'vue'

const props = defineProps({ fileInfo: Object, waveData: Object })

// ── Canvas ────────────────────────────────────────────────────────────────────
const canvas = ref(null)
const CLASS_COLORS = {
  kick: '#e06c75', snare: '#ECA72C', hihat: '#7ec8c8', clap: '#7ecb8f', tom: '#c084fc',
}
const classColor = cls => CLASS_COLORS[cls] || '#ECA72C'

const features    = computed(() => props.fileInfo?.features      || [])
const featureNames = computed(() => props.fileInfo?.feature_names || [])
const maxAbs      = computed(() => Math.max(...features.value.map(Math.abs), 1e-6))
const pct         = i  => Math.min(100, Math.abs(features.value[i] ?? 0) / maxAbs.value * 100)
const fmtVal      = v  => v == null ? '—' : Number(v).toFixed(4)

watch(() => props.waveData, async () => {
  await nextTick()
  if (canvas.value && props.waveData) drawWaveform()
})

function drawWaveform() {
  const c = canvas.value
  const color = classColor(props.fileInfo.label)
  c.width  = c.offsetWidth * window.devicePixelRatio
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

// ── Opisy cech ────────────────────────────────────────────────────────────────
const FEAT_DESC = {
  // Spektralne
  spectral_centroid_mean: {
    short: 'Środek widma — średnia',
    detail: '"Jasność" dźwięku. Wyższe = jaśniejszy (hihat), niższe = ciemniejszy (kick). Obliczany jako ważona średnia częstotliwości.',
    drums: { kick: 'niska', hihat: 'wysoka', snare: 'średnia' },
  },
  spectral_centroid_std: {
    short: 'Środek widma — wariancja',
    detail: 'Jak bardzo "jasność" zmienia się w czasie trwania sample. Duża wartość = dynamicznie zmieniająca się barwa.',
  },
  spectral_bandwidth_mean: {
    short: 'Szerokość pasma — średnia',
    detail: 'Rozpiętość częstotliwości w sygnale. Szerokie pasmo = bogaty dźwięk (szum). Wąskie = czysty, skupiony ton.',
    drums: { clap: 'szerokie', kick: 'wąskie', hihat: 'szerokie' },
  },
  spectral_bandwidth_std: {
    short: 'Szerokość pasma — wariancja',
    detail: 'Zmienność szerokości pasma. Drzewo używa tej cechy jako pierwszego rozgałęzienia — oddziela clap od reszty.',
  },
  spectral_rolloff_mean: {
    short: 'Rolloff 85% — średnia',
    detail: 'Częstotliwość, poniżej której skupia się 85% energii widmowej. Kick ma niski rolloff (mało wysokich), hihat wysoki.',
    drums: { kick: '~2 kHz', hihat: '~10 kHz', snare: '~6 kHz' },
  },
  spectral_rolloff_std: {
    short: 'Rolloff 85% — wariancja',
    detail: 'Zmienność rolloff w czasie. Dźwięki o szybkim ataku i zaniku (perkusja) mają dużą wariancję rolloff.',
  },
  spectral_flatness_mean: {
    short: 'Płaskość widma — średnia',
    detail: 'Miara "szumowości". 0 = czysty ton (kick), 1 = biały szum. Cymbal/hihat jest bardziej płaski niż kick.',
    drums: { kick: '~0.02', hihat: '~0.25', clap: '~0.15' },
  },
  spectral_flatness_std: {
    short: 'Płaskość widma — wariancja',
    detail: 'Zmienność płaskości. Dźwięki z wyraźnym atakiem mają dużą wariancję (widmo zmienia się od tonu do szumu).',
  },

  // Energia
  rms_mean: {
    short: 'Energia RMS — średnia',
    detail: 'Średnia głośność (Root Mean Square amplitudy). Kick ma wysokie RMS ze względu na silny, basowy atak.',
    drums: { kick: 'wysoka', hihat: 'niska', tom: 'wysoka' },
  },
  rms_std: {
    short: 'Energia RMS — wariancja',
    detail: 'Jak szybko dźwięk opada (decay). Perkusja ma duże RMS_std — energia gwałtownie rośnie i zanika.',
  },
  zero_crossing_rate_mean: {
    short: 'ZCR — średnia',
    detail: 'Liczba przejść sygnału przez zero na sekundę (znormalizowana). Szumy/cymbal = dużo; basowe tony = mało.',
    drums: { kick: 'niska', hihat: 'wysoka', clap: 'średnia' },
  },
  zero_crossing_rate_std: {
    short: 'ZCR — wariancja',
    detail: 'Zmienność liczby przejść przez zero. Dźwięki ze zmienną barwą w czasie mają dużą wartość.',
  },

  // Czas / rytm
  onset_strength_mean: {
    short: 'Siła ataku — średnia',
    detail: 'Jak gwałtowny jest impuls dźwięku (zmiana energii między klatkami). Cała perkusja ma naturalnie silny atak.',
  },
  onset_strength_std: {
    short: 'Siła ataku — wariancja',
    detail: 'Zmienność siły ataku — przydatne gdy sample zawiera kilka uderzeń lub dźwięk ma nieregularny przebieg.',
  },
  tempo: {
    short: 'Tempo (BPM)',
    detail: 'Estymowane tempo w uderzeniach na minutę. Dla pojedynczych, krótkich sampli jest mało wiarygodne — librosa szacuje z wewnętrznych fluktuacji.',
  },

  // Chroma
  chroma_mean: {
    short: 'Chroma — średnia',
    detail: 'Średni profil harmoniczny (12 klas: C, C#, D, ..., B). Kick/hihat mają niskie chroma — brak wyraźnego tonu. Tom może mieć nieco wyższe.',
  },
  chroma_std: {
    short: 'Chroma — wariancja',
    detail: 'Zmienność profilu harmonicznego. Instrumenty perkusyjne bez stałej wysokości (hihat) mają dużą wariancję chroma.',
  },
}




// ── Tooltip przy hover ────────────────────────────────────────────────────────
const hovered   = ref(null)
const mousePos  = reactive({ x: 0, y: 0 })

const hoveredDesc = computed(() => hovered.value ? FEAT_DESC[hovered.value] ?? null : null)

const ttStyle = computed(() => ({
  left: Math.min(mousePos.x + 16, window.innerWidth - 320) + 'px',
  top:  mousePos.y - 10 + 'px',
}))

function onMouseMove(e) { mousePos.x = e.clientX; mousePos.y = e.clientY }

watch(hovered, v => {
  if (v) window.addEventListener('mousemove', onMouseMove)
  else   window.removeEventListener('mousemove', onMouseMove)
})
</script>

<style scoped>
.wp-root { display: flex; flex-direction: column; gap: 0; }

/* ── Nagłówek ─────────────────────────────────────────────────────────────── */
.wp-file-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.wp-filename {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--text);
}
.wp-meta {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--mono);
  margin-left: auto;
}

/* ── Siatka kart ──────────────────────────────────────────────────────────── */
.feat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 7px;
  padding: 0 2px;
  margin-top: 12px;
}

/* ── Karta cechy ──────────────────────────────────────────────────────────── */
.feat-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 11px;
  cursor: default;
  transition: border-color .15s, background .15s;
}
.feat-card--hovered {
  border-color: var(--accent);
  background: rgba(236, 167, 44, 0.05);
}

.feat-card-top { margin-bottom: 5px; }

.feat-friendly {
  display: block;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.feat-raw {
  display: block;
  font-family: var(--mono);
  font-size: 9px;
  color: var(--text3);
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feat-bar-wrap {
  height: 4px;
  background: var(--bg3);
  border-radius: 2px;
  margin-bottom: 4px;
}
.feat-bar { height: 4px; border-radius: 2px; transition: width .5s; }

.feat-val {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text);
}

/* ── Tooltip ─────────────────────────────────────────────────────────────── */
.feat-tooltip {
  position: fixed;
  z-index: 200;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 10px;
  padding: 12px 15px;
  max-width: 300px;
  pointer-events: none;
  box-shadow: 0 6px 24px rgba(0,0,0,.6);
}
.tt-title {
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 6px;
}
.tt-body {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.55;
}
.tt-drum {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}
.tt-drum-chip {
  font-family: var(--mono);
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid;
  font-weight: 600;
}
.tt-drum-chip.kick  { color: var(--kick);  border-color: var(--kick);  background: rgba(224,108,117,.12); }
.tt-drum-chip.snare { color: var(--snare); border-color: var(--snare); background: rgba(236,167,44, .12); }
.tt-drum-chip.hihat { color: var(--hihat); border-color: var(--hihat); background: rgba(126,200,200,.12); }
.tt-drum-chip.clap  { color: var(--clap);  border-color: var(--clap);  background: rgba(126,203,143,.12); }
.tt-drum-chip.tom   { color: var(--tom);   border-color: var(--tom);   background: rgba(192,132,252,.12); }

/* Tooltip transition */
.tt-fade-enter-active, .tt-fade-leave-active { transition: opacity .15s, transform .15s; }
.tt-fade-enter-from, .tt-fade-leave-to { opacity: 0; transform: translateY(4px); }
</style>
