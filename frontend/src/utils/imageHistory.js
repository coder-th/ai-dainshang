/**
 * 图片生成历史 - API 持久化工具
 *
 * 图片 base64 数据直接存储在后端 SQLite（通过 Django REST API）。
 * 如果生成结果是 http/https 链接，前端通过 canvas 将其转为 base64 后再保存。
 *
 * 导出函数：
 *   createThumbnail(base64, maxSize)        - 缩略图压缩（canvas）
 *   compressImageBlob(blob, maxSize)        - Blob → 压缩 base64
 *   compressImageDataUri(dataUri, maxSize)  - data URI → 压缩 base64
 *   loadImageHistory()                      - 拉取最近 30 天历史
 *   appendImageHistory(record)              - 新建一条历史记录
 *   deleteImageHistoryRecord(id)            - 删除单条
 *   clearAllImageHistory()                  - 清空所有历史
 */

import { imageHistoryApi } from '@/api/index.js'

// ─── 图片压缩工具（纯浏览器端）────────────────────────────────────────────────

/**
 * 将 base64 图片压缩为小缩略图（用于参考图预览）。
 * @param {string} base64   原始 base64（data URI 格式）
 * @param {number} maxSize  缩略图最大宽/高（px），默认 80
 * @returns {Promise<string>} 压缩后的 data URI，失败时返回空字符串
 */
export function createThumbnail(base64, maxSize = 80) {
  return new Promise((resolve) => {
    if (!base64) { resolve(''); return }
    const img = new Image()
    img.onload = () => {
      const canvas  = document.createElement('canvas')
      const ratio   = Math.min(maxSize / img.width, maxSize / img.height, 1)
      canvas.width  = Math.round(img.width  * ratio)
      canvas.height = Math.round(img.height * ratio)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', 0.7))
    }
    img.onerror = () => resolve('')
    img.src = base64
  })
}

/**
 * 将 Blob 对象压缩为 base64 data URI（用于保存生成结果图片）。
 * @param {Blob}   blob     图片 Blob
 * @param {number} maxSize  最大宽/高（px），默认 1024
 * @returns {Promise<string>} 压缩后的 data URI，失败时返回空字符串
 */
export function compressImageBlob(blob, maxSize = 1024) {
  return new Promise((resolve) => {
    if (!blob) { resolve(''); return }
    const url = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      const canvas  = document.createElement('canvas')
      const ratio   = Math.min(maxSize / img.width, maxSize / img.height, 1)
      canvas.width  = Math.round(img.width  * ratio)
      canvas.height = Math.round(img.height * ratio)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', 0.85))
    }
    img.onerror = () => { URL.revokeObjectURL(url); resolve('') }
    img.src = url
  })
}

/**
 * 将 data URI 压缩为指定尺寸的 base64 data URI。
 * @param {string} dataUri  原始 data URI
 * @param {number} maxSize  最大宽/高（px），默认 1024
 * @returns {Promise<string>} 压缩后的 data URI，失败时返回空字符串
 */
export function compressImageDataUri(dataUri, maxSize = 1024) {
  return new Promise((resolve) => {
    if (!dataUri) { resolve(''); return }
    const img = new Image()
    img.onload = () => {
      const canvas  = document.createElement('canvas')
      const ratio   = Math.min(maxSize / img.width, maxSize / img.height, 1)
      canvas.width  = Math.round(img.width  * ratio)
      canvas.height = Math.round(img.height * ratio)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', 0.85))
    }
    img.onerror = () => resolve('')
    img.src = dataUri
  })
}

// ─── 字段映射：服务端 snake_case ↔ 前端 camelCase ────────────────────────────

/** 服务端响应 → 前端 Record */
function _fromServer(r) {
  return {
    id:               r.id,
    createdAt:        r.created_at,
    model:            r.model,
    modelName:        r.model_name,
    provider:         r.provider         || '',
    prompt:           r.prompt,
    aspectRatio:      r.aspect_ratio     || '',
    imageSize:        r.image_size       || '',
    search:           r.search           ?? false,
    baseImageThumbs:  r.base_image_thumbs || [],
    refImageThumbs:   r.ref_image_thumbs  || [],
    results:          r.results           || [],
    status:           r.status,
    generationTimeMs: r.generation_time_ms ?? 0,
  }
}

/** 前端 Record → 服务端 payload */
function _toServer(record) {
  return {
    model:              record.model,
    model_name:         record.modelName,
    provider:           record.provider          || '',
    prompt:             record.prompt,
    aspect_ratio:       record.aspectRatio        || '',
    image_size:         record.imageSize          || '',
    search:             record.search             ?? false,
    base_image_thumbs:  record.baseImageThumbs    || [],
    ref_image_thumbs:   record.refImageThumbs     || [],
    results:            record.results            || [],
    status:             record.status,
    generation_time_ms: record.generationTimeMs   ?? 0,
  }
}

// ─── CRUD ─────────────────────────────────────────────────────────────────────

/**
 * 拉取最近 30 天的图片历史记录（服务端按 created_at 降序排列）。
 * @returns {Promise<Object[]>}
 */
export async function loadImageHistory() {
  try {
    const { data } = await imageHistoryApi.list()
    return (data.results ?? data).map(_fromServer)
  } catch (e) {
    console.warn('[ImageHistory] 获取历史失败:', e)
    return []
  }
}

/**
 * 将一条图片历史记录写入数据库。
 * @param {Object} record  前端 camelCase 格式的记录对象
 */
export async function appendImageHistory(record) {
  try {
    await imageHistoryApi.create(_toServer(record))
  } catch (e) {
    console.warn('[ImageHistory] 保存历史失败:', e)
  }
}

/**
 * 删除指定 id 的历史记录。
 * @param {number} id
 */
export async function deleteImageHistoryRecord(id) {
  await imageHistoryApi.delete(id)
}

/**
 * 清空所有图片历史记录。
 */
export async function clearAllImageHistory() {
  await imageHistoryApi.clearAll()
}
