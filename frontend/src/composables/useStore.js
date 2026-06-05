import { reactive, computed } from 'vue'

const API = ''

const state = reactive({
  files: [],
  trainedModel: null,
  lastFileId: null,
  toasts: [],
})

export function useStore() {
  const classCounts = computed(() => {
    const counts = {}
    state.files.forEach(f => { counts[f.label] = (counts[f.label] || 0) + 1 })
    return counts
  })

  const readyToTrain = computed(() =>
    Object.keys(classCounts.value).length >= 2 && state.files.length >= 4
  )

  function toast(msg, type = 'ok') {
    const id = Date.now()
    state.toasts.push({ id, msg, type })
    setTimeout(() => { state.toasts = state.toasts.filter(t => t.id !== id) }, 3000)
  }

  async function uploadBatch(files, label) {
    const fd = new FormData()
    fd.append('label', label)
    for (const f of files) fd.append('files', f)
    const r = await fetch(API + '/upload-batch', { method: 'POST', body: fd })
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail) }
    const data = await r.json()
    for (const f of data.files) { state.files.push(f); state.lastFileId = f.file_id }
    if (data.errors > 0) toast(`Wgrano ${data.uploaded}, błędy: ${data.errors}`, 'err')
    else toast(`Wgrano ${data.uploaded} plik(ów) jako "${label}"`)
    return data
  }

  async function deleteFile(fileId) {
    await fetch(API + '/files/' + fileId, { method: 'DELETE' })
    state.files = state.files.filter(f => f.file_id !== fileId)
    toast('Usunięto plik')
  }

  async function trainModel(params) {
    const r = await fetch(API + '/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail) }
    const data = await r.json()
    state.trainedModel = data
    toast(`Drzewo wytrenowane! Accuracy: ${data.evaluation.quality.accuracy_pct.toFixed(1)}%`)
    return data
  }

  async function predict(file) {
    const fd = new FormData()
    fd.append('file', file)
    const r = await fetch(API + '/predict', { method: 'POST', body: fd })
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail) }
    return r.json()
  }

  async function exportResults() {
    const r = await fetch(API + '/export')
    if (!r.ok) throw new Error('Błąd eksportu')
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'wynik_klasyfikatora.json'; a.click()
    URL.revokeObjectURL(url)
    toast('Wyniki wyeksportowane!')
  }

  return { state, classCounts, readyToTrain, toast, uploadBatch, deleteFile, trainModel, predict, exportResults }
}
