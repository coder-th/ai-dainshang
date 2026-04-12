/**
 * 视频生成历史 - API 持久化工具
 *
 * 数据存储在后端 SQLite（通过 Django REST API），不再使用 localStorage。
 *
 * 导出函数：
 *   createThumbnail(base64, maxSize)  - 浏览器端缩略图压缩（canvas，无 I/O）
 *   loadHistory()                     - 拉取最近 30 天历史（服务端过滤）
 *   appendHistory(record)             - 新建一条历史记录
 *   deleteHistoryRecord(id)           - 删除单条（id 为服务端自增整数）
 *   clearAllHistory()                 - 清空所有历史
 */

import { historyApi } from '@/api/index.js'

// ─── 缩略图生成（纯浏览器端，无需改动）─────────────────────────────────────────

/**
 * 将 base64 图片压缩为小缩略图，减少传输数据量。
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

// ─── 字段映射：服务端 snake_case ↔ 前端 camelCase ────────────────────────────

/** 服务端响应 → 前端 Record */
function _fromServer(r) {
  return {
    id:               r.id,
    createdAt:        r.created_at,
    model:            r.model,
    modelName:        r.model_name,
    prompt:           r.prompt,
    thumbnails:       r.thumbnails  || [],
    imageCount:       r.image_count,
    ratio:            r.ratio,
    duration:         r.duration,
    taskId:           r.task_id     || null,
    status:           r.status,
    videoUrl:         r.video_url   || null,
    videoPath:        r.video_path  || null,
    error:            r.error       || null,
    generationTimeMs: r.generation_time_ms,
    enhancedPrompt:   r.enhanced_prompt  || '',
    videoFileSize:    r.video_file_size  || '',
  }
}

/** 前端 Record → 服务端 payload */
function _toServer(record) {
  return {
    model:              record.model,
    model_name:         record.modelName,
    prompt:             record.prompt,
    thumbnails:         record.thumbnails       || [],
    image_count:        record.imageCount       ?? 0,
    ratio:              record.ratio            || '',
    duration:           record.duration         ?? 8,
    task_id:            record.taskId           || null,
    status:             record.status,
    video_url:          record.videoUrl         || null,
    video_path:         record.videoPath        || null,
    error:              record.error            || null,
    generation_time_ms: record.generationTimeMs ?? 0,
    enhanced_prompt:    record.enhancedPrompt   || '',
    video_file_size:    record.videoFileSize     || '',
  }
}

// ─── CRUD（均为 async，调用方负责 await / fire-and-forget）──────────────────

/**
 * 拉取最近 30 天的历史记录（服务端按 created_at 降序排列）。
 * @returns {Promise<Object[]>}
 */
export async function loadHistory() {
  try {
    const { data } = await historyApi.list()
    return (data.results ?? data).map(_fromServer)
  } catch (e) {
    console.warn('[VideoHistory] 获取历史失败:', e)
    return []
  }
}

/**
 * 将一条历史记录写入数据库。
 * @param {Object} record  前端 camelCase 格式的记录对象
 */
export async function appendHistory(record) {
  try {
    await historyApi.create(_toServer(record))
  } catch (e) {
    console.warn('[VideoHistory] 保存历史失败:', e)
  }
}

/**
 * 删除指定 id 的历史记录（id 为服务端自增整数）。
 * @param {number} id
 */
export async function deleteHistoryRecord(id) {
  await historyApi.delete(id)
}

/**
 * 清空所有历史记录。
 */
export async function clearAllHistory() {
  await historyApi.clearAll()
}
