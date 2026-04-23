/**
 * AI 供应商注册表
 *
 * 新增供应商：在 PROVIDERS 数组中追加一个对象即可，无需修改其他文件。
 * - id:          供应商唯一标识（与模型配置中的 provider 字段对应）
 * - name:        UI 显示名称
 * - storageKey:  localStorage 存储 API Key 的键名
 * - placeholder: API Key 输入框的占位文本
 */

/** @type {Array<{id:string, name:string, storageKey:string, placeholder:string}>} */
export const PROVIDERS = [
  {
    id: 'lingy',
    name: '灵芽AI（图片）',
    storageKey: 'api_key_lingy',
    placeholder: '请输入灵芽AI的 API Key（图片生成）',
  },
  {
    id: 'lingy_video',
    name: '灵芽AI（视频）',
    storageKey: 'api_key_lingy_video',
    placeholder: '请输入灵芽AI的 API Key（视频生成）',
  },
  {
    id: 'yunwu',
    name: '云雾AI（图片）',
    storageKey: 'api_key_yunwu',
    placeholder: '请输入云雾AI的 API Key（图片生成）',
  },
  {
    id: 'yunwu_video',
    name: '云雾AI（视频）',
    storageKey: 'api_key_yunwu_video',
    placeholder: '请输入云雾AI的 API Key（视频生成）',
  },
  {
    id: 'yunwu_gpt',
    name: '云雾AI（GPT图像）',
    storageKey: 'api_key_yunwu_gpt',
    placeholder: '请输入云雾AI的 API Key（GPT 图像生成）',
  },
]

/** 按 id 查找供应商配置，未找到时返回第一个 */
export function getProviderById(id) {
  return PROVIDERS.find(p => p.id === id) ?? PROVIDERS[0]
}

/** 读取指定供应商的 API Key（从 localStorage） */
export function getApiKey(providerId) {
  return localStorage.getItem(getProviderById(providerId).storageKey) || ''
}

/** 保存指定供应商的 API Key（到 localStorage） */
export function saveApiKey(providerId, key) {
  localStorage.setItem(getProviderById(providerId).storageKey, key)
}
