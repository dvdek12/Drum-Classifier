<template>
  <div class="tree-panel" ref="panelEl">

    <!-- Animacja trenowania -->
    <TreeBuildAnimation v-if="training" />

    <!-- Pusty stan (nie trenuje i brak drzewa) -->
    <div v-else-if="!hasTree" class="tree-empty">
      <div class="empty-icon">🌳</div>
      <p>Wytrenuj drzewo, żeby zobaczyć wizualizację</p>
    </div>

    <template v-else>
      <!-- Toolbar -->
      <div class="tree-toolbar">
        <button class="tree-btn" @click="fitToView">⊡ Dopasuj</button>
        <button class="tree-btn" @click="resetZoom">1:1</button>
        <span class="tree-info">
          {{ layout.nodes.length }} węzłów ·
          głębokość {{ treeDepth }} ·
          {{ leafNodes.length }} liści
        </span>
        <span class="tree-hint">scroll = zoom · drag = pan</span>
      </div>

      <!-- SVG canvas -->
      <svg
        :width="svgW" :height="svgH"
        style="display:block; flex:1"
        @mousedown.prevent="startDrag"
      >
        <g :transform="`translate(${pan.x},${pan.y}) scale(${pan.scale})`">
          <!-- Krawędzie (pod węzłami) -->
          <TreeEdge
            v-for="(link, i) in links" :key="'e' + i"
            :sourceX="link.source._px" :sourceY="link.source._py"
            :targetX="link.target._px" :targetY="link.target._py"
            :nodeW="NODE_W" :nodeH="NODE_H"
            :isLeft="link.isLeft"
          />
          <!-- Węzły wewnętrzne -->
          <TreeNodeInternal
            v-for="n in internalNodes" :key="'n' + n._id"
            :node="n" :x="n._px" :y="n._py"
            :W="NODE_W" :H="NODE_H"
            @tooltip="onTooltip"
          />
          <!-- Liście -->
          <TreeLeaf
            v-for="n in leafNodes" :key="'l' + n._id"
            :node="n" :x="n._px" :y="n._py"
            :W="NODE_W" :H="NODE_H"
            @tooltip="onTooltip"
          />
        </g>
      </svg>

      <!-- Tooltip -->
      <Transition name="tooltip-fade">
        <div
          v-if="tooltip"
          class="node-tooltip"
          :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
          v-html="tooltip.html"
        />
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import TreeEdge           from './TreeEdge.vue'
import TreeNodeInternal   from './TreeNode.vue'
import TreeLeaf           from './TreeLeaf.vue'
import TreeBuildAnimation from './TreeBuildAnimation.vue'

// ─── Props ────────────────────────────────────────────────────────────────────
const props = defineProps({
  treeData: Object,   // state.trainedModel = { tree: { params, feature_names, classes, tree: rootNode }, evaluation, … }
  visible:  Boolean,
  training: { type: Boolean, default: false },
})

// ─── Stałe layoutu ────────────────────────────────────────────────────────────
const NODE_W = 180
const NODE_H = 90
const H_GAP  = 36   // poziomy odstęp między slotami
const V_GAP  = 72   // pionowy odstęp między poziomami

// ─── Stan ─────────────────────────────────────────────────────────────────────
const panelEl = ref(null)
const svgW    = ref(800)
const svgH    = ref(600)
const pan     = ref({ x: 40, y: 40, scale: 1 })
const tooltip = ref(null)

// ─── Walidacja danych ─────────────────────────────────────────────────────────
// API: /train → { tree: { params, feature_names, classes, tree: <rootNode> }, evaluation, … }
// Stąd właściwy korzeń drzewa to treeData.tree.tree
const hasTree = computed(() => !!(props.treeData?.tree?.tree))
const rootNode = computed(() => props.treeData?.tree?.tree ?? null)

// ─── Algorytm layoutu (Reingold-Tilford uproszczony) ─────────────────────────
let _idCnt = 0

function layoutTree(node, depth, counter) {
  node._id    = _idCnt++
  node._depth = depth

  if (node.is_leaf || !node.left) {
    node._x = counter.val++
    return
  }
  layoutTree(node.left,  depth + 1, counter)
  layoutTree(node.right, depth + 1, counter)
  node._x = (node.left._x + node.right._x) / 2
}

function collectAll(node, parent, nodesArr, linksArr) {
  nodesArr.push(node)
  if (parent) {
    linksArr.push({
      source: parent,
      target: node,
      isLeft: parent.left === node,
    })
  }
  if (!node.is_leaf && node.left)  collectAll(node.left,  node, nodesArr, linksArr)
  if (!node.is_leaf && node.right) collectAll(node.right, node, nodesArr, linksArr)
}

const layout = computed(() => {
  if (!hasTree.value) return { nodes: [], links: [] }

  _idCnt = 0
  const root    = rootNode.value
  const counter = { val: 0 }
  layoutTree(root, 0, counter)

  const nodesArr = []
  const linksArr = []
  collectAll(root, null, nodesArr, linksArr)

  // Pozycje pikselowe: _px = lewy górny róg węzła
  nodesArr.forEach(n => {
    n._px = n._x * (NODE_W + H_GAP) + H_GAP
    n._py = n._depth * (NODE_H + V_GAP) + V_GAP / 2
  })

  return { nodes: nodesArr, links: linksArr }
})

const links         = computed(() => layout.value.links)
const internalNodes = computed(() => layout.value.nodes.filter(n => !n.is_leaf))
const leafNodes     = computed(() => layout.value.nodes.filter(n =>  n.is_leaf))
const treeDepth     = computed(() =>
  layout.value.nodes.length
    ? Math.max(...layout.value.nodes.map(n => n._depth))
    : 0
)

// ─── Fit to view ──────────────────────────────────────────────────────────────
function fitToView() {
  const nodes = layout.value.nodes
  if (!nodes.length || !svgW.value || !svgH.value) return

  const padding = 48
  const xs = nodes.map(n => n._px)
  const ys = nodes.map(n => n._py)
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs) + NODE_W
  const y0 = Math.min(...ys)
  const y1 = Math.max(...ys) + NODE_H

  const contentW = x1 - x0
  const contentH = y1 - y0

  const scaleX = (svgW.value - padding * 2) / contentW
  const scaleY = (svgH.value - padding * 2) / contentH
  const scale  = Math.min(scaleX, scaleY, 1.2)

  pan.value = {
    x: (svgW.value - contentW * scale) / 2 - x0 * scale,
    y: padding - y0 * scale,
    scale,
  }
}

function resetZoom() {
  pan.value = { x: 40, y: 40, scale: 1 }
}

// ─── Resize ───────────────────────────────────────────────────────────────────
function updateSize() {
  if (!panelEl.value) return
  svgW.value = panelEl.value.clientWidth
  svgH.value = panelEl.value.clientHeight
}

watch(
  () => props.treeData,
  async () => {
    await nextTick()
    updateSize()
    await nextTick()
    fitToView()
  },
)

watch(
  () => props.visible,
  async (v) => {
    if (!v) return
    await nextTick()
    updateSize()
    await nextTick()
    fitToView()
  },
)

onMounted(() => {
  updateSize()
  if (hasTree.value) fitToView()
  window.addEventListener('resize',    updateSize)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup',   stopDrag)
})

onUnmounted(() => {
  window.removeEventListener('resize',    updateSize)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup',   stopDrag)
})

// ─── Pan ──────────────────────────────────────────────────────────────────────
const dragging = ref(false)
let dragStart  = { x: 0, y: 0, px: 0, py: 0 }

function startDrag(e) {
  dragging.value = true
  dragStart = { x: e.clientX, y: e.clientY, px: pan.value.x, py: pan.value.y }
  if (panelEl.value) panelEl.value.style.cursor = 'grabbing'
}
function onMouseMove(e) {
  if (!dragging.value) return
  pan.value = {
    ...pan.value,
    x: dragStart.px + (e.clientX - dragStart.x),
    y: dragStart.py + (e.clientY - dragStart.y),
  }
}
function stopDrag() {
  if (!dragging.value) return
  dragging.value = false
  if (panelEl.value) panelEl.value.style.cursor = 'grab'
}

// ─── Zoom kółkiem ──────────────────────────────────────────────────────────────
function onWheel(e) {
  e.preventDefault()
  const rect  = panelEl.value.getBoundingClientRect()
  const mx    = e.clientX - rect.left
  const my    = e.clientY - rect.top
  const delta = e.deltaY < 0 ? 1.12 : 0.89
  const ns    = Math.min(4, Math.max(0.08, pan.value.scale * delta))
  pan.value   = {
    scale: ns,
    x: mx - (mx - pan.value.x) * (ns / pan.value.scale),
    y: my - (my - pan.value.y) * (ns / pan.value.scale),
  }
}

onMounted(()  => panelEl.value?.addEventListener('wheel', onWheel, { passive: false }))
onUnmounted(() => panelEl.value?.removeEventListener('wheel', onWheel))

// ─── Tooltip ──────────────────────────────────────────────────────────────────
function onTooltip(data) {
  if (!data) { tooltip.value = null; return }
  tooltip.value = {
    html: data.html,
    x:    data.event.clientX + 16,
    y:    data.event.clientY - 20,
  }
}
</script>

<style scoped>
.tree-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  cursor: grab;
  user-select: none;
  position: relative;
  background: var(--bg);
}

/* ── Toolbar ── */
.tree-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--bg2);
  cursor: default;
}
.tree-btn {
  padding: 3px 11px;
  border-radius: 5px;
  border: 1px solid var(--border2);
  background: transparent;
  color: var(--text2);
  font-size: 11px;
  font-family: var(--mono);
  cursor: pointer;
  transition: .15s;
  line-height: 1.6;
}
.tree-btn:hover { border-color: var(--accent); color: var(--accent); }
.tree-info  { font-size: 11px; font-family: var(--mono); color: var(--text2); }
.tree-hint  { font-size: 10px; font-family: var(--mono); color: var(--text3); margin-left: auto; }

/* ── Tooltip ── */
.node-tooltip {
  position: fixed;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 12px;
  font-family: var(--mono);
  pointer-events: none;
  z-index: 100;
  max-width: 240px;
  line-height: 1.6;
  box-shadow: 0 4px 16px rgba(0,0,0,.5);
}
.tooltip-fade-enter-active,
.tooltip-fade-leave-active { transition: opacity .12s; }
.tooltip-fade-enter-from,
.tooltip-fade-leave-to    { opacity: 0; }
</style>
