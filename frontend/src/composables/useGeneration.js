import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { generateApi } from '@/api/index.js'

function _buildProxyUrl(remoteUrl) {
  const base = import.meta.env.DEV ? '/api' : `${window.location.origin}/api`
  return `${base}/proxy-image/?url=${encodeURIComponent(remoteUrl)}`
}

function _formatBytes(bytes) {
  if (!bytes || bytes <= 0) return null
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function _fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function _startFakeProgress(task) {
  const start = Date.now()
  task._intervalId = setInterval(() => {
    const elapsed = (Date.now() - start) / 1000
    task.progress = Math.min(95, Math.round(100 * (1 - Math.exp(-elapsed / 28))))
  }, 500)
}

function _stopFakeProgress(task, success) {
  if (task._intervalId) {
    clearInterval(task._intervalId)
    task._intervalId = null
  }
  task.progress = success ? 100 : task.progress
}

/**
 * 图像生成任务管理 Composable
 *
 * @param {{ baseImages, referenceImages, currentModelId, params, showSettings }} deps
 */
export function useGeneration({ baseImages, referenceImages, currentModelId, prompt, params, showSettings }) {
  const generationTasks = ref([])
  const isGenerating = ref(false)
  const isBatchSaving = ref(false)
  const preview = ref({ visible: false, urls: [], index: 0 })

  const doneTaskCount = computed(() =>
    generationTasks.value.filter(t => t.status === 'done').length
  )

  const allSelected = computed({
    get() {
      const done = generationTasks.value.filter(t => t.status === 'done')
      return done.length > 0 && done.every(t => t.selected)
    },
    set(val) {
      generationTasks.value.forEach(t => { if (t.status === 'done') t.selected = val })
    },
  })

  const selectedDoneCount = computed(() =>
    generationTasks.value.filter(t => t.status === 'done' && t.selected).length
  )

  async function _executeTask(task, baseB64, refB64s) {
    task.status = 'loading'
    task.doneAt = null
    task.fileSize = null
    _startFakeProgress(task)
    const storedKey = localStorage.getItem('ai_api_key') || ''
    const t0 = Date.now()
    try {
      const resp = await generateApi.generate({
        api_key: storedKey,
        model: currentModelId.value,
        prompt: prompt.value,
        aspect_ratio: params.aspectRatio,
        image_size: params.resolution,
        search: params.webAccess === 'true',
        base_images: [baseB64],
        ref_images: refB64s,
      })
      const result = resp.data.results?.[0]
      if (result?.error) throw new Error(result.error)
      _stopFakeProgress(task, true)
      task.resultUrl = result.url
      task.doneAt = `${((Date.now() - t0) / 1000).toFixed(1)}s`
      // 代理拉取图片，同时获取大小并缓存 blob
      try {
        const proxyResp = await fetch(_buildProxyUrl(result.url))
        const cl = proxyResp.headers.get('content-length')
        task._blob = await proxyResp.blob()
        task.fileSize = _formatBytes(cl ? parseInt(cl) : task._blob.size)
      } catch { task.fileSize = null }
      task.status = 'done'
    } catch (e) {
      _stopFakeProgress(task, false)
      task.error = e.response?.data?.error || e.message || '生成失败'
      task.status = 'error'
    }
  }

  async function handleGenerate() {
    const storedKey = localStorage.getItem('ai_api_key') || ''
    if (!storedKey) {
      ElMessage.warning('请先配置 API 密钥')
      showSettings.value = true
      return
    }
    if (baseImages.value.length === 0) {
      ElMessage.warning('请至少上传一张基准图片')
      return
    }
    if (!prompt.value?.trim()) {
      ElMessage.warning('请填写创意描述')
      return
    }

    isGenerating.value = true

    let refB64s = []
    try {
      refB64s = await Promise.all(referenceImages.value.map(img => _fileToBase64(img.file)))
    } catch {
      ElMessage.error('参考图片处理失败')
      isGenerating.value = false
      return
    }

    generationTasks.value = baseImages.value.map((img, i) => ({
      id: `${Date.now()}-${i}`,
      index: i,
      baseImage: img,
      status: 'pending',
      progress: 0,
      resultUrl: null,
      doneAt: null,
      fileSize: null,
      selected: true,
      error: null,
      _intervalId: null,
      _blob: null,
    }))

    await Promise.allSettled(
      generationTasks.value.map(async (task) => {
        try {
          const baseB64 = await _fileToBase64(task.baseImage.file)
          await _executeTask(task, baseB64, refB64s)
        } catch {
          task.status = 'error'
          task.error = '图片处理失败'
        }
      })
    )

    isGenerating.value = false
    const done = doneTaskCount.value
    if (done > 0) {
      ElMessage.success(`${done}/${generationTasks.value.length} 张图片生成完成`)
    }
  }

  async function retryTask(task) {
    const storedKey = localStorage.getItem('ai_api_key') || ''
    if (!storedKey) { showSettings.value = true; return }
    task.error = null
    task.progress = 0
    try {
      const refB64s = await Promise.all(referenceImages.value.map(img => _fileToBase64(img.file)))
      const baseB64 = await _fileToBase64(task.baseImage.file)
      await _executeTask(task, baseB64, refB64s)
    } catch {
      task.status = 'error'
      task.error = '重试失败'
    }
  }

  function openResultPreview(clickedTask) {
    const done = generationTasks.value.filter(t => t.status === 'done')
    const idx = done.findIndex(t => t.id === clickedTask.id)
    preview.value = {
      visible: true,
      urls: done.map(t => t.resultUrl),
      index: Math.max(0, idx),
    }
  }

  async function downloadResult(task) {
    try {
      const blob = task._blob ?? await (await fetch(_buildProxyUrl(task.resultUrl))).blob()
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = task.resultUrl.split('/').pop()?.split('?')[0] || `result-${task.index + 1}.jpg`
      a.click()
      URL.revokeObjectURL(blobUrl)
    } catch {
      ElMessage.error('下载失败，请右键图片另存为')
    }
  }

  async function batchSaveResults() {
    const selected = generationTasks.value.filter(t => t.status === 'done' && t.selected)
    if (!selected.length) return
    isBatchSaving.value = true
    let successCount = 0
    for (const task of selected) {
      try {
        await downloadResult(task)
        successCount++
        await new Promise(r => setTimeout(r, 300))
      } catch {
        ElMessage.warning(`第 ${task.index + 1} 张下载失败`)
      }
    }
    isBatchSaving.value = false
    if (successCount > 0) ElMessage.success(`已保存 ${successCount} 张图片`)
  }

  return {
    generationTasks,
    isGenerating,
    isBatchSaving,
    preview,
    doneTaskCount,
    allSelected,
    selectedDoneCount,
    handleGenerate,
    retryTask,
    openResultPreview,
    downloadResult,
    batchSaveResults,
  }
}
