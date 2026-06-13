<template>
  <div class="ba-wrap">

    <!-- Header -->
    <div class="ba-header">
      <div class="ba-indicator">
        <div class="ba-ring" />
        <div class="ba-core" />
      </div>
      <Transition name="st-fade" mode="out-in">
        <span :key="statusIdx" class="ba-status">{{ STATUS[statusIdx] }}</span>
      </Transition>
    </div>

    <!-- Tree SVG -->
    <svg class="ba-svg" :viewBox="`0 0 ${VW} ${VH}`" preserveAspectRatio="xMidYMid meet">
      <defs>
        <filter id="ba-glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <linearGradient id="ba-scan-grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stop-color="#ECA72C" stop-opacity="0" />
          <stop offset="40%"  stop-color="#ECA72C" stop-opacity="0.6" />
          <stop offset="60%"  stop-color="#ECA72C" stop-opacity="0.6" />
          <stop offset="100%" stop-color="#ECA72C" stop-opacity="0" />
        </linearGradient>
      </defs>

      <!-- Horizontal scan line sweeping down -->
      <rect class="ba-scanline" x="0" :width="VW" height="1.5"
        fill="url(#ba-scan-grad)" />

      <!-- ── Edges ─────────────────────────────────────────────────── -->
      <path
        v-for="(e, i) in EDGES" :key="`e${i}`"
        :d="e.path" pathLength="1"
        class="ba-edge" :class="{ drawn: edgesVis[i] }"
        :stroke="e.isLeft ? '#4a7a5a' : '#7a4a55'"
        fill="none" stroke-width="2" stroke-linecap="round"
      />

      <!-- Edge condition labels (fade in with edge) -->
      <g v-for="(e, i) in EDGES" :key="`el${i}`"
        class="ba-edge-label" :class="{ shown: edgesVis[i] }">
        <text :x="e.lx" :y="e.ly"
          text-anchor="middle" font-size="12" font-weight="700"
          font-family="'Jost',monospace"
          :fill="e.isLeft ? '#7ecb8f' : '#e06c75'"
        >{{ e.isLeft ? '≤' : '>' }}</text>
      </g>

      <!-- Particles flowing down edges -->
      <template v-for="(e, i) in EDGES" :key="`ep${i}`">
        <circle v-if="edgesVis[i]" r="2.5"
          :fill="e.isLeft ? '#7ecb8f' : '#e06c75'" opacity="0.6">
          <animateMotion :dur="`${e.pdur}s`" repeatCount="indefinite" :path="e.path" />
        </circle>
        <circle v-if="edgesVis[i]" r="1.5"
          :fill="e.isLeft ? '#7ecb8f' : '#e06c75'" opacity="0.3">
          <animateMotion :dur="`${e.pdur}s`" repeatCount="indefinite"
            :path="e.path" :begin="`${(e.pdur * 0.55).toFixed(2)}s`" />
        </circle>
      </template>

      <!-- ── Nodes ──────────────────────────────────────────────────── -->
      <g v-for="(n, i) in NODES" :key="`n${i}`"
        :transform="`translate(${n.cx},${n.cy})`">
        <g class="ba-node" :class="{ shown: nodesVis[i], leaf: n.isLeaf }">

          <!-- Drop shadow -->
          <rect :x="-HW+2" :y="-HH+3" :width="NW" :height="NH" rx="8"
            :fill="n.isLeaf ? n.color : '#0a0810'" opacity="0.28" />

          <!-- Body -->
          <rect :x="-HW" :y="-HH" :width="NW" :height="NH" rx="8"
            :fill="n.bg" :stroke="n.color" stroke-width="1.5"
            :filter="n.isLeaf && nodesVis[i] ? 'url(#ba-glow)' : null"
          />

          <!-- Class distribution bar (top strip) -->
          <rect v-for="(s, j) in n.segs" :key="j"
            :x="-HW + 5 + s.x" :y="-HH + 5" :width="s.w" height="4" rx="2"
            :fill="s.color" />

          <!-- Primary label: feature name or drum class -->
          <text x="0" :y="n.isLeaf ? -3 : -8"
            text-anchor="middle" font-family="'Jost',monospace"
            :font-size="n.isLeaf ? 18 : 9.5"
            :font-weight="n.isLeaf ? 700 : 400"
            letter-spacing="0.5"
            :fill="n.isLeaf ? n.color : '#c9a96e'"
          >{{ n.line1 }}</text>

          <!-- Secondary label: threshold or 'n=X' -->
          <text x="0" :y="n.isLeaf ? 13 : 10"
            text-anchor="middle" font-family="'Jost',monospace"
            :font-size="n.isLeaf ? 9 : 14"
            :font-weight="n.isLeaf ? 400 : 700"
            :fill="n.isLeaf ? '#7a6650' : '#f5ecd7'"
          >{{ n.line2 }}</text>

          <!-- Stats line -->
          <text x="0" y="26"
            text-anchor="middle" font-family="'Jost',monospace"
            font-size="8" fill="#584a5a"
          >n={{ n.samples }} · imp={{ n.imp }}</text>

          <!-- Node ID badge (bottom-right) -->
          <text :x="HW - 5" :y="HH - 5"
            text-anchor="end" font-family="'Jost',monospace"
            font-size="8" fill="#3d2e4f"
          >#{{ n.id }}</text>
        </g>
      </g>
    </svg>

    <!-- Bouncing dots -->
    <div class="ba-footer">
      <span v-for="k in 4" :key="k" class="ba-dot"
        :style="`animation-delay:${(k - 1) * 0.18}s`" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// ── Constants ────────────────────────────────────────────────────────────────
const VW = 700, VH = 425
const NW = 136, NH = 66
const HW = NW / 2, HH = NH / 2   // half-width / half-height

const CC = {
  kick:  '#e06c75', snare: '#ECA72C', hihat: '#7ec8c8',
  clap:  '#7ecb8f', tom:   '#c084fc',
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function distSegs(dist, total) {
  const bw = NW - 10
  let x = 0
  return Object.entries(dist).map(([c, n]) => {
    const w = (n / total) * bw
    const s = { x, w: Math.max(1, Math.round(w)), color: CC[c] ?? '#6b7280' }
    x += w
    return s
  })
}

function bez(sx, sy, tx, ty) {
  const my = (sy + ty) / 2
  return `M${sx},${sy} C${sx},${my} ${tx},${my} ${tx},${ty}`
}

// ── Node definitions (based on real test_tree.json) ──────────────────────────
// Depth 0: cy=52  (bottom = 85)
// Depth 1: cy=165 (top = 132, bottom = 198)
// Depth 2: cy=278 (top = 245, bottom = 311)
// Depth 3: cy=374 (top = 341)

const NODES = [
  // ── Internal nodes ──
  {
    id: 1, cx: 350, cy: 52, isLeaf: false,
    color: '#5a4878', bg: '#31263e', shadowFill: '#0a0810',
    line1: 'sp_bw_σ', line2: '≤ 147.59', samples: 21, imp: '2.267',
    segs: distSegs({ clap: 5, hihat: 3, kick: 6, snare: 4, tom: 3 }, 21),
  },
  {
    id: 2, cx: 200, cy: 165, isLeaf: false,
    color: '#5a4878', bg: '#31263e', shadowFill: '#0a0810',
    line1: 'sp_bw_σ', line2: '≤ 49.40', samples: 11, imp: '1.540',
    segs: distSegs({ clap: 5, hihat: 3, tom: 3 }, 11),
  },
  {
    id: 7, cx: 520, cy: 165, isLeaf: false,
    color: '#5a4878', bg: '#31263e', shadowFill: '#0a0810',
    line1: 'sp_centroid_μ', line2: '≤ 5124', samples: 10, imp: '0.971',
    segs: distSegs({ kick: 6, snare: 4 }, 10),
  },
  {
    id: 4, cx: 310, cy: 278, isLeaf: false,
    color: '#5a4878', bg: '#31263e', shadowFill: '#0a0810',
    line1: 'sp_centroid_μ', line2: '≤ 6261', samples: 6, imp: '1.000',
    segs: distSegs({ hihat: 3, tom: 3 }, 6),
  },
  // ── Leaf nodes ──
  {
    id: 3, cx: 95, cy: 278, isLeaf: true,
    color: CC.clap, bg: CC.clap + '1e', shadowFill: CC.clap,
    line1: 'CLAP', line2: 'pure', samples: 5, imp: '0',
    segs: distSegs({ clap: 5 }, 5),
  },
  {
    id: 8, cx: 450, cy: 278, isLeaf: true,
    color: CC.kick, bg: CC.kick + '1e', shadowFill: CC.kick,
    line1: 'KICK', line2: 'pure', samples: 6, imp: '0',
    segs: distSegs({ kick: 6 }, 6),
  },
  {
    id: 9, cx: 595, cy: 278, isLeaf: true,
    color: CC.snare, bg: CC.snare + '1e', shadowFill: CC.snare,
    line1: 'SNARE', line2: 'pure', samples: 4, imp: '0',
    segs: distSegs({ snare: 4 }, 4),
  },
  {
    id: 5, cx: 255, cy: 374, isLeaf: true,
    color: CC.tom, bg: CC.tom + '1e', shadowFill: CC.tom,
    line1: 'TOM', line2: 'pure', samples: 3, imp: '0',
    segs: distSegs({ tom: 3 }, 3),
  },
  {
    id: 6, cx: 370, cy: 374, isLeaf: true,
    color: CC.hihat, bg: CC.hihat + '1e', shadowFill: CC.hihat,
    line1: 'HIHAT', line2: 'pure', samples: 3, imp: '0',
    segs: distSegs({ hihat: 3 }, 3),
  },
]

// ── Edge definitions ─────────────────────────────────────────────────────────
// Node index map: 0=N1root, 1=N2, 2=N7, 3=N4, 4=N3clap, 5=N8kick, 6=N9snare, 7=N5tom, 8=N6hihat
function makeEdge(srcIdx, tgtIdx, isLeft) {
  const s = NODES[srcIdx], t = NODES[tgtIdx]
  const sx = s.cx, sy = s.cy + HH
  const tx = t.cx, ty = t.cy - HH
  const lx = sx + (tx - sx) * 0.33
  const ly = sy + (ty - sy) * 0.33 - 4
  const dist = Math.hypot(tx - sx, ty - sy)
  return {
    path: bez(sx, sy, tx, ty),
    isLeft, lx, ly,
    pdur: +(0.65 + dist / 350).toFixed(2),
  }
}

const EDGES = [
  makeEdge(0, 1, true),   // root → N2
  makeEdge(0, 2, false),  // root → N7
  makeEdge(1, 4, true),   // N2 → CLAP
  makeEdge(1, 3, false),  // N2 → N4
  makeEdge(2, 5, true),   // N7 → KICK
  makeEdge(2, 6, false),  // N7 → SNARE
  makeEdge(3, 7, true),   // N4 → TOM
  makeEdge(3, 8, false),  // N4 → HIHAT
]

// ── Animation sequence: [type, index, delay_ms] ──────────────────────────────
// Build BFS: root → left subtree → right subtree
const SEQ = [
  ['n', 0,    0],          // root
  ['e', 0,  420], ['n', 1,  700],   // left branch
  ['e', 1,  920], ['n', 2, 1200],   // right branch
  ['e', 2, 1500], ['n', 4, 1780],   // CLAP leaf
  ['e', 3, 1960], ['n', 3, 2220],   // N4 internal
  ['e', 4, 2430], ['n', 5, 2710],   // KICK leaf
  ['e', 5, 2870], ['n', 6, 3120],   // SNARE leaf
  ['e', 6, 3300], ['n', 7, 3550],   // TOM leaf
  ['e', 7, 3680], ['n', 8, 3920],   // HIHAT leaf
  // full tree visible at ~4100ms, cycle restarts at 6300ms
]
const CYCLE_MS = 6300

// ── Status messages ───────────────────────────────────────────────────────────
const STATUS = [
  'Analizowanie próbek audio...',
  'Obliczanie zysku informacyjnego...',
  'Szukanie najlepszego podziału...',
  'Budowanie gałęzi drzewa...',
  'Obliczanie Information Gain / Gain Ratio...',
  'Walidacja modelu...',
]

// ── Reactive state ────────────────────────────────────────────────────────────
const nodesVis  = ref(Array(NODES.length).fill(false))
const edgesVis  = ref(Array(EDGES.length).fill(false))
const statusIdx = ref(0)

let timers    = []
let cycleT    = null
let statusT   = null

function runCycle() {
  nodesVis.value = Array(NODES.length).fill(false)
  edgesVis.value = Array(EDGES.length).fill(false)

  for (const [type, idx, ms] of SEQ) {
    const t = setTimeout(() => {
      if (type === 'n') nodesVis.value[idx] = true
      else              edgesVis.value[idx] = true
    }, ms)
    timers.push(t)
  }

  cycleT = setTimeout(() => {
    timers.forEach(clearTimeout)
    timers = []
    runCycle()
  }, CYCLE_MS)
}

onMounted(() => {
  runCycle()
  statusT = setInterval(() => {
    statusIdx.value = (statusIdx.value + 1) % STATUS.length
  }, 1700)
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
  clearTimeout(cycleT)
  clearInterval(statusT)
})
</script>

<style scoped>
/* ── Container ─────────────────────────────────────────────────────────────── */
.ba-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18px 16px 12px;
  overflow: hidden;
  background: var(--bg);
  user-select: none;
}

/* ── Header ────────────────────────────────────────────────────────────────── */
.ba-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  height: 28px;
}

/* Pulsing indicator dot */
.ba-indicator {
  position: relative;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ba-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(236, 167, 44, 0.18);
  animation: ba-ring-pulse 1.6s ease-in-out infinite;
}
.ba-core {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  position: relative;
  animation: ba-core-pulse 1.6s ease-in-out infinite;
}
@keyframes ba-ring-pulse {
  0%, 100% { transform: scale(1);   opacity: 0.9; }
  50%       { transform: scale(1.5); opacity: 0.4; }
}
@keyframes ba-core-pulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(0.8); }
}

/* Status text with fade transition */
.ba-status {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--text2);
  white-space: nowrap;
}
.st-fade-enter-active, .st-fade-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}
.st-fade-enter-from { opacity: 0; transform: translateY(6px); }
.st-fade-leave-to   { opacity: 0; transform: translateY(-6px); }

/* ── SVG canvas ─────────────────────────────────────────────────────────────── */
.ba-svg {
  width: 100%;
  flex: 1;
  min-height: 0;
  max-width: 720px;
  overflow: visible;
}

/* Horizontal scan line animation */
.ba-scanline {
  animation: ba-scan 2.4s linear infinite;
  pointer-events: none;
}
@keyframes ba-scan {
  0%   { transform: translateY(-2px); opacity: 0; }
  5%   { opacity: 1; }
  90%  { opacity: 0.7; }
  100% { transform: translateY(427px); opacity: 0; }
}

/* ── Edges ─────────────────────────────────────────────────────────────────── */
.ba-edge {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  transition: stroke-dashoffset 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}
.ba-edge.drawn {
  stroke-dashoffset: 0;
}

/* Edge condition labels */
.ba-edge-label {
  opacity: 0;
  transition: opacity 0.4s ease 0.3s;  /* delay slightly after edge draws */
}
.ba-edge-label.shown {
  opacity: 1;
}

/* ── Nodes ─────────────────────────────────────────────────────────────────── */
.ba-node {
  transform-box: fill-box;
  transform-origin: center center;
  transform: scale(0);
  opacity: 0;
  transition:
    transform 0.42s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity   0.28s ease-out;
}
.ba-node.shown {
  transform: scale(1);
  opacity: 1;
}

/* Leaf nodes breathe gently when shown */
.ba-node.shown.leaf rect:nth-child(2) {
  animation: ba-leaf-breathe 2.5s ease-in-out infinite;
}
@keyframes ba-leaf-breathe {
  0%, 100% { stroke-opacity: 1;   stroke-width: 1.5px; }
  50%       { stroke-opacity: 0.5; stroke-width: 2.5px; }
}

/* ── Footer dots ───────────────────────────────────────────────────────────── */
.ba-footer {
  display: flex;
  gap: 7px;
  margin-top: 10px;
}
.ba-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: ba-dot-bounce 1.1s ease-in-out infinite;
  opacity: 0.7;
}
@keyframes ba-dot-bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
  40%            { transform: scale(1);   opacity: 1; }
}
</style>
