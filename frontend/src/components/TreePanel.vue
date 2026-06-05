<template>
  <div class="tree-panel" ref="panelEl">
    <div v-if="!treeData" class="tree-empty">
      wytrenuj drzewo żeby zobaczyć wizualizację
    </div>
    <template v-else>
      <svg
        :width="svgW" :height="svgH"
        style="display:block"
        @mousedown.prevent="startDrag"
      >
        <g :transform="`translate(${pan.x},${pan.y}) scale(${pan.scale})`">
          <!-- Krawędzie -->
          <TreeEdge
            v-for="(link, i) in links" :key="'e'+i"
            :sourceX="link.source._px" :sourceY="link.source._py"
            :targetX="link.target._px" :targetY="link.target._py"
            :nodeW="NODE_W" :nodeH="NODE_H"
            :isLeft="link.source.left === link.target"
          />
          <!-- Węzły wewnętrzne -->
          <TreeNode
            v-for="n in internalNodes" :key="'n'+n._id"
            :node="n" :x="n._px" :y="n._py"
            :W="NODE_W" :H="NODE_H"
            @tooltip="onTooltip"
          />
          <!-- Liście -->
          <TreeLeaf
            v-for="n in leafNodes" :key="'l'+n._id"
            :node="n" :x="n._px" :y="n._py"
            :W="NODE_W" :H="NODE_H"
            @tooltip="onTooltip"
          />
        </g>
      </svg>

      <!-- Tooltip -->
      <div
        v-if="tooltip"
        class="node-tooltip"
        style="opacity:1"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
        v-html="tooltip.html"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import TreeEdge from './TreeEdge.vue'
import TreeNode from './TreeNode.vue'
import TreeLeaf from './TreeLeaf.vue'

const props = defineProps({ treeData: Object, visible: Boolean })

const NODE_W = 160, NODE_H = 56, H_GAP = 24, V_GAP = 60

const panelEl = ref(null)
const svgW = ref(800)
const svgH = ref(600)
const pan = ref({ x: 0, y: 20, scale: 1 })
const tooltip = ref(null)

// ── Layout ──────────────────────────────────────────────
let _idCounter = 0
function layoutTree(node, depth = 0, counter = { val: 0 }) {
  node._id = _idCounter++
  node._depth = depth
  if (node.is_leaf || !node.left) { node._x = counter.val++; return }
  layoutTree(node.left,  depth + 1, counter)
  layoutTree(node.right, depth + 1, counter)
  node._x = (node.left._x + node.right._x) / 2
}

function collectNodes(node, parent = null, nodesArr = [], linksArr = []) {
  nodesArr.push(node)
  if (parent) linksArr.push({ source: parent, target: node })
  if (!node.is_leaf && node.left)  collectNodes(node.left,  node, nodesArr, linksArr)
  if (!node.is_leaf && node.right) collectNodes(node.right, node, nodesArr, linksArr)
  return { nodesArr, linksArr }
}

const layout = computed(() => {
  if (!props.treeData) return { nodes: [], links: [], W: 0, H: 0 }
  _idCounter = 0
  const root = props.treeData.tree
  layoutTree(root)
  const { nodesArr, linksArr } = collectNodes(root)
  const maxX = Math.max(...nodesArr.map(n => n._x))
  const maxD = Math.max(...nodesArr.map(n => n._depth))
  const W = Math.max(900, (maxX + 1) * (NODE_W + H_GAP))
  const H = (maxD + 1) * (NODE_H + V_GAP) + 40
  nodesArr.forEach(n => {
    n._px = n._x * (NODE_W + H_GAP) + NODE_W / 2
    n._py = n._depth * (NODE_H + V_GAP) + 20
  })
  return { nodes: nodesArr, links: linksArr, W, H }
})

const links        = computed(() => layout.value.links)
const internalNodes = computed(() => layout.value.nodes.filter(n => !n.is_leaf))
const leafNodes    = computed(() => layout.value.nodes.filter(n => n.is_leaf))

// ── Resize ───────────────────────────────────────────────
function updateSize() {
  if (!panelEl.value) return
  svgW.value = panelEl.value.clientWidth
  svgH.value = panelEl.value.clientHeight
}

watch(() => props.treeData, () => {
  pan.value = { x: 20, y: 20, scale: 1 }
})

watch(() => props.visible, async (v) => {
  if (v) {
    await nextTick()
    updateSize()
  }
})

onMounted(() => {
  updateSize()
  window.addEventListener('resize', updateSize)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopDrag)
})
onUnmounted(() => {
  window.removeEventListener('resize', updateSize)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopDrag)
})

// ── Pan ──────────────────────────────────────────────────
const dragging = ref(false)
let dragStart = { x: 0, y: 0, px: 0, py: 0 }

function startDrag(e) {
  dragging.value = true
  dragStart = { x: e.clientX, y: e.clientY, px: pan.value.x, py: pan.value.y }
  panelEl.value.style.cursor = 'grabbing'
}
function onMouseMove(e) {
  if (!dragging.value) return
  pan.value.x = dragStart.px + (e.clientX - dragStart.x)
  pan.value.y = dragStart.py + (e.clientY - dragStart.y)
}
function stopDrag() {
  if (dragging.value) {
    dragging.value = false
    if (panelEl.value) panelEl.value.style.cursor = 'grab'
  }
}

// ── Zoom ─────────────────────────────────────────────────
function onWheel(e) {
  e.preventDefault()
  const rect = panelEl.value.getBoundingClientRect()
  const mx = e.clientX - rect.left, my = e.clientY - rect.top
  const delta = e.deltaY < 0 ? 1.1 : 0.9
  const ns = Math.min(3, Math.max(0.15, pan.value.scale * delta))
  pan.value.x = mx - (mx - pan.value.x) * (ns / pan.value.scale)
  pan.value.y = my - (my - pan.value.y) * (ns / pan.value.scale)
  pan.value.scale = ns
}

onMounted(() => {
  panelEl.value?.addEventListener('wheel', onWheel, { passive: false })
})
onUnmounted(() => {
  panelEl.value?.removeEventListener('wheel', onWheel)
})

// ── Tooltip ──────────────────────────────────────────────
function onTooltip(data) {
  if (!data) { tooltip.value = null; return }
  tooltip.value = { html: data.html, x: data.event.clientX + 12, y: data.event.clientY - 20 }
}
</script>
