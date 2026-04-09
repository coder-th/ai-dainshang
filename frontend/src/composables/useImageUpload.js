import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
const LIMITS = { base: 10, ref: 8 }

export function useImageUpload() {
  const baseImages = ref([])
  const referenceImages = ref([])
  const dragState = reactive({ list: null, srcIdx: null, overIdx: null })
  const preview = reactive({ visible: false, urls: [], index: 0 })

  function _getList(type) {
    return type === 'ref' ? referenceImages : baseImages
  }

  function _validateFile(file, list, limit) {
    if (list.value.length >= limit) {
      ElMessage.warning(`最多上传 ${limit} 张图片`)
      return false
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      ElMessage.error('仅支持 PNG、JPG、JPEG、WEBP 格式')
      return false
    }
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.error('图片大小不能超过 10MB')
      return false
    }
    return true
  }

  async function onFileChange(e, type) {
    const list = _getList(type)
    const limit = LIMITS[type]
    const files = Array.from(e.target.files || [])
    for (const file of files) {
      if (!_validateFile(file, list, limit)) break
      const url = URL.createObjectURL(file)
      // 上传时立即缓存 base64，避免后续多次调用 FileReader 或 file 对象失效
      const b64 = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      list.value.push({ uid: `${Date.now()}-${Math.random()}`, name: file.name, url, file, b64 })
    }
    e.target.value = ''
  }

  function removeImg(type, idx) {
    const list = _getList(type)
    const img = list.value[idx]
    if (img?.url?.startsWith('blob:')) URL.revokeObjectURL(img.url)
    list.value.splice(idx, 1)
  }

  // ── 拖拽排序 ────────────────────────────────────────
  function onDragStart(type, idx) {
    dragState.list = type
    dragState.srcIdx = idx
  }

  function onDragOver(type, idx) {
    if (dragState.list === type) dragState.overIdx = idx
  }

  function onDrop(type, idx) {
    if (dragState.list !== type || dragState.srcIdx === null || dragState.srcIdx === idx) return
    const list = _getList(type)
    const items = [...list.value]
    const [moved] = items.splice(dragState.srcIdx, 1)
    items.splice(idx, 0, moved)
    list.value = items
    onDragEnd()
  }

  function onDragEnd() {
    dragState.list = null
    dragState.srcIdx = null
    dragState.overIdx = null
  }

  // ── 预览 ────────────────────────────────────────────
  function openPreview(list, idx) {
    preview.urls = list.map(img => img.url)
    preview.index = idx
    preview.visible = true
  }

  return {
    baseImages,
    referenceImages,
    dragState,
    preview,
    onFileChange,
    removeImg,
    onDragStart,
    onDragOver,
    onDrop,
    onDragEnd,
    openPreview,
  }
}
