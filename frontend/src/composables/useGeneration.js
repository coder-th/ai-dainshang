import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { generateApi } from '@/api/index.js'
import { getApiKey } from '@/config/providers.js'
import { getImageModelById } from '@/config/models.js'
import { appendImageHistory, compressImageBlob, compressImageDataUri, createThumbnail } from '@/utils/imageHistory.js'

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

/** 从 blob URL 提取后缀，用于批量保存时命名 */
function _extFromUrl(url) {
  const clean = url?.split('?')[0] ?? ''
  const m = clean.match(/\.([a-zA-Z0-9]+)$/)
  return m ? `.${m[1].toLowerCase()}` : '.jpg'
}

/** 生成批量保存子文件夹名称：MM-DD-HH-mm */
function _folderName() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}-${pad(d.getHours())}-${pad(d.getMinutes())}`
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
 * @param {{ baseImages, referenceImages, currentModelId, currentProviderId, prompt, params, showSettings, settingsActiveProvider }} deps
 */
export function useGeneration({ baseImages, referenceImages, currentModelId, currentProviderId, prompt, params, showSettings, settingsActiveProvider }) {
  const generationTasks = ref([])
  const isGenerating = ref(false)
  const isBatchSaving = ref(false)
  const preview = ref({ visible: false, urls: [], index: 0 })

  // ─── 历史记录保存（fire-and-forget）────────────────────────────────────────
  async function _saveHistory(tasks, generationTimeMs) {
    try {
      const results = await Promise.all(tasks.map(async (task) => {
        let image_data = ''
        if (task.status === 'done') {
          if (task._blob) {
            image_data = await compressImageBlob(task._blob, 1024)
          } else if (task.resultUrl?.startsWith('data:')) {
            image_data = await compressImageDataUri(task.resultUrl, 1024)
          }
          // http/https 且 blob 获取失败时 image_data 保持空字符串
        }
        return {
          index:      task.index,
          image_data,
          error:      task.error    || null,
          file_size:  task.fileSize || '',
          done_at:    task.doneAt   || null,
        }
      }))

      const doneCount = tasks.filter(t => t.status === 'done').length
      const errCount  = tasks.filter(t => t.status === 'error').length
      const status    = errCount === 0 ? 'done' : doneCount === 0 ? 'error' : 'partial'

      const baseImageThumbs = await Promise.all(
        baseImages.value.map(img => createThumbnail(img.b64))
      )
      const refImageThumbs = await Promise.all(
        referenceImages.value.map(img => createThumbnail(img.b64))
      )

      const modelConfig = getImageModelById(currentModelId.value)
      appendImageHistory({
        model:            currentModelId.value,
        modelName:        modelConfig.name,
        provider:         currentProviderId.value,
        prompt:           prompt.value,
        aspectRatio:      params.aspectRatio  || '',
        imageSize:        params.resolution   || '',
        search:           params.webAccess === 'true',
        baseImageThumbs,
        refImageThumbs,
        results,
        status,
        generationTimeMs,
      })
    } catch (e) {
      console.warn('[ImageHistory] 保存历史失败:', e)
    }
  }

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

  function _openSettings() {
    if (settingsActiveProvider) {
      settingsActiveProvider.value = currentProviderId.value
    }
    showSettings.value = true
  }

  async function _executeTask(task, baseB64, refB64s) {
    task.status = 'loading'
    task.doneAt = null
    task.fileSize = null
    _startFakeProgress(task)
    const storedKey = getApiKey(currentProviderId.value)
    const t0 = Date.now()
    try {
      const resp = await generateApi.generate({
        api_key: storedKey,
        provider: currentProviderId.value,
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
    const storedKey = getApiKey(currentProviderId.value)
    if (!storedKey) {
      ElMessage.warning('请先配置 API 密钥')
      _openSettings()
      return
    }
    if (!prompt.value?.trim()) {
      ElMessage.warning('请填写创意描述')
      return
    }

    isGenerating.value = true

    // 直接读取上传时已缓存的 b64，不再重新读取 file 对象
    const refB64s = referenceImages.value.map(img => img.b64)

    const isTextToImage = baseImages.value.length === 0

    if (isTextToImage) {
      generationTasks.value = [{
        id: `${Date.now()}-0`,
        index: 0,
        baseImage: null,
        status: 'pending',
        progress: 0,
        resultUrl: null,
        doneAt: null,
        fileSize: null,
        selected: true,
        error: null,
        _intervalId: null,
        _blob: null,
      }]
      const task = generationTasks.value[0]
      task.status = 'loading'
      _startFakeProgress(task)
      const t0 = Date.now()
      try {
        const resp = await generateApi.generate({
          api_key: storedKey,
          provider: currentProviderId.value,
          model: currentModelId.value,
          prompt: prompt.value,
          aspect_ratio: params.aspectRatio,
          image_size: params.resolution,
          search: params.webAccess === 'true',
          base_images: [],
          ref_images: refB64s,
        })
        const result = resp.data.results?.[0]
        if (result?.error) throw new Error(result.error)
        _stopFakeProgress(task, true)
        task.resultUrl = result.url
        task.doneAt = `${((Date.now() - t0) / 1000).toFixed(1)}s`
        try {
          const proxyResp = await fetch(_buildProxyUrl(result.url))
          const cl = proxyResp.headers.get('content-length')
          task._blob = await proxyResp.blob()
          task.fileSize = _formatBytes(cl ? parseInt(cl) : task._blob.size)
        } catch { task.fileSize = null }
        task.status = 'done'
        ElMessage.success('图片生成完成')
      } catch (e) {
        _stopFakeProgress(task, false)
        task.error = e.response?.data?.error || e.message || '生成失败'
        task.status = 'error'
      }
      isGenerating.value = false
      _saveHistory([task], Date.now() - t0)  // fire-and-forget
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

    const batchT0 = Date.now()
    await Promise.allSettled(
      generationTasks.value.map(async (task) => {
        const baseB64 = task.baseImage.b64
        await _executeTask(task, baseB64, refB64s)
      })
    )
    const batchElapsedMs = Date.now() - batchT0

    isGenerating.value = false
    const done = doneTaskCount.value
    if (done > 0) {
      ElMessage.success(`${done}/${generationTasks.value.length} 张图片生成完成`)
    }
    _saveHistory(generationTasks.value, batchElapsedMs)  // fire-and-forget
  }

  async function retryTask(task) {
    const storedKey = getApiKey(currentProviderId.value)
    if (!storedKey) { _openSettings(); return }
    task.error = null
    task.progress = 0
    const refB64s = referenceImages.value.map(img => img.b64)
    const baseB64 = task.baseImage?.b64 ?? null
    await _executeTask(task, baseB64, refB64s)
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

  /**
   * 批量保存：使用 File System Access API 写入用户指定目录下的子文件夹。
   * 子文件夹命名为 MM-DD-HH-mm，每张图命名为 result-1.jpg / result-2.jpg …
   * 若浏览器不支持 showDirectoryPicker，降级为逐个下载。
   */
  async function batchSaveResults() {
    const selected = generationTasks.value.filter(t => t.status === 'done' && t.selected)
    if (!selected.length) return

    isBatchSaving.value = true

    // 尝试 File System Access API
    if (typeof window.showDirectoryPicker === 'function') {
      try {
        const rootHandle = await window.showDirectoryPicker({ mode: 'readwrite' })
        const subFolderName = _folderName()
        const subHandle = await rootHandle.getDirectoryHandle(subFolderName, { create: true })

        let successCount = 0
        for (const task of selected) {
          try {
            const blob = task._blob ?? await (await fetch(_buildProxyUrl(task.resultUrl))).blob()
            const ext = _extFromUrl(task.resultUrl)
            const fileName = `result-${task.index + 1}${ext}`
            const fileHandle = await subHandle.getFileHandle(fileName, { create: true })
            const writable = await fileHandle.createWritable()
            await writable.write(blob)
            await writable.close()
            successCount++
          } catch {
            ElMessage.warning(`第 ${task.index + 1} 张保存失败`)
          }
        }
        isBatchSaving.value = false
        if (successCount > 0) ElMessage.success(`已保存 ${successCount} 张到文件夹 ${subFolderName}`)
        return
      } catch (e) {
        // 用户取消选择文件夹
        if (e?.name === 'AbortError') {
          isBatchSaving.value = false
          return
        }
        // 其他错误降级
      }
    }

    // 降级：逐个触发浏览器下载
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
