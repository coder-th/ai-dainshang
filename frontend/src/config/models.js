/**
 * 模型能力配置表
 *
 * 每个模型声明自己支持的参数范围，前端参数面板根据当前选中模型动态过滤选项。
 * 新增模型：在 IMAGE_MODELS 数组中追加一个对象即可，无需修改其他文件。
 * 新增供应商：在 src/config/providers.js 中注册，然后在模型对象中设置对应的 provider 字段。
 */

// ─── 全局选项字典 ──────────────────────────────────────────────────────────────

export const RATIO_OPTIONS = [
  { label: '自动', value: 'auto' },
  { label: '1:1 (正方形 - 头像/Ins)', value: '1:1' },
  { label: '4:3 (标准 - 传统相机/iPad)', value: '4:3' },
  { label: '3:4 (标准 - 通用竖屏)', value: '3:4' },
  { label: '16:9 (宽屏 - 电脑/视频)', value: '16:9' },
  { label: '9:16 (全面屏 - 手机/短视频)', value: '9:16' },
  { label: '3:2 (经典 - 单反/照片)', value: '3:2' },
  { label: '2:3 (经典 - 竖版照片)', value: '2:3' },
  { label: '5:4 (中画幅 - 证件照/打印)', value: '5:4' },
  { label: '4:5 (小红书/Ins流媒体)', value: '4:5' },
  { label: '21:9 (超宽屏 - 电影感)', value: '21:9' },
  { label: '4:1 (宽幅 - 网页头图/横条幅)', value: '4:1' },
  { label: '1:4 (竖幅 - 侧边栏/长条图)', value: '1:4' },
  { label: '8:1 (超宽幅 - 全景横图)', value: '8:1' },
  { label: '1:8 (超竖幅 - 全景竖图)', value: '1:8' },
]

export const SIZE_OPTIONS = [
  { label: '0.5K', value: '512' },
  { label: '1K（默认）', value: '1K' },
  { label: '2K', value: '2K' },
  { label: '4K', value: '4K' },
]

// ─── 图像模型配置 ──────────────────────────────────────────────────────────────

/**
 * @typedef {Object} ImageModelConfig
 * @property {string}   id               API 传参使用的 model 字符串
 * @property {string}   name             显示名称
 * @property {string}   provider         供应商 id（对应 providers.js 中的 PROVIDERS[].id）
 * @property {string}   tag              分类标签
 * @property {string}   desc             模型描述
 * @property {boolean}  disabled         是否禁用（灰显，不可选）
 * @property {string[]} supportedRatios  支持的比例 value 列表
 * @property {string[]} supportedSizes   支持的分辨率 value 列表
 * @property {boolean}  supportsSearch   是否支持联网检索
 * @property {string}   defaultRatio     默认比例
 * @property {string}   defaultSize      默认分辨率
 */

/** @type {ImageModelConfig[]} */
export const IMAGE_MODELS = [
  // ── 灵芽AI 模型 ──────────────────────────────────────────────────────────────
  {
    id: 'nano-banana-2',
    name: 'Nano-banana 2 (通用)',
    provider: 'lingy',
    tag: '通用',
    disabled: false,
    desc: 'Nano Banana 2 是 Google 于 2026 年 2 月发布的新一代 AI 图像生成工具，内部代号 Gemini 3.1 Flash Image。将 Nano Banana Pro 的专业级画质与 Gemini Flash 的极致速度完美结合，具备先进的世界知识、精准文本渲染能力。',
    supportedRatios: ['auto', '1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', '5:4', '4:5', '21:9', '4:1', '1:4'],
    supportedSizes: ['1K', '2K', '4K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'nano-banana-pro',
    name: 'Nano-banana Pro (通用)',
    provider: 'lingy',
    tag: '通用',
    disabled: false,
    desc: '谷歌 Nano Banana Pro 是基于 Gemini 3 Pro 的图像生成模型，支持融合 14 张素材并保持 5 个人物一致性，可输出 4K 分辨率。具备工作室级局部编辑、光线焦点控制及精准文本渲染能力，可连接 Google 搜索实时数据。',
    supportedRatios: ['auto', '1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', '5:4', '4:5', '21:9', '4:1', '1:4'],
    supportedSizes: ['1K', '2K', '4K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '2K',
  },
  {
    id: 'nano-banana',
    name: 'Nano-banana (通用)',
    provider: 'lingy',
    tag: '通用',
    disabled: false,
    desc: '谷歌 Gemini 2.5 Flash Image，人物一致性极强，光影逻辑合理，照片级逼真。擅长角色特征保持，多轮编辑不"失忆"。',
    supportedRatios: ['auto', '1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'seedream-5.0',
    name: 'Seedream-5.0 (通用)',
    provider: 'lingy',
    tag: '通用',
    disabled: false,
    desc: 'Doubao-Seedream-5.0-lite 是字节跳动发布的最新图像创作模型。首次搭载联网检索功能，能融合实时网络信息，提升生图时效性。',
    supportedRatios: ['auto', '1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', '4:5'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'seedream-4.5',
    name: 'Seedream-4.5 (通用)',
    provider: 'lingy',
    tag: '通用',
    disabled: false,
    desc: '豆包 Seedream 4.5 图像模型，主体一致性、指令精准度、空间逻辑理解及美学表现力全面迭代，强化多图组合与高清图文混排能力。',
    supportedRatios: ['1:1', '4:3', '3:4', '16:9', '9:16'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'z-image-turbo',
    name: 'Z-image-turbo (生图)',
    provider: 'lingy',
    tag: '生图',
    disabled: false,
    desc: '阿里最新开源模型，速度超快——8 步就能画完一张图，效果炸裂——海报上的小字、Logo 里的中英文都能清晰生成，画人像时连头发丝、皮肤质感都超真实。',
    supportedRatios: ['1:1', '4:3', '3:4', '16:9', '9:16'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: '1:1',
    defaultSize: '1K',
  },
  {
    id: 'qwen-image-max',
    name: 'Qwen-image-max (生图)',
    provider: 'lingy',
    tag: '生图',
    disabled: false,
    desc: '通义千问图像生成模型 Max 系列，大幅降低生成图片的 AI 感，提升图像真实性；具备更真实的人物质感、更细腻的自然纹理、更美观的文字渲染。',
    supportedRatios: ['auto', '1:1', '4:3', '3:4', '16:9', '9:16'],
    supportedSizes: ['1K', '2K', '4K'],
    supportsSearch: false,
    defaultRatio: '1:1',
    defaultSize: '1K',
  },
  {
    id: 'qwen-image-edit-max',
    name: 'Qwen-image-edit-max (修图)',
    provider: 'lingy',
    tag: '修图',
    disabled: false,
    desc: '通义千问图像编辑模型 Max 系列，提升工业设计与几何推理能力；提升角色一致性；集成 LoRA 能力，可进行更多功能的图像编辑。',
    supportedRatios: ['auto'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: 'auto',
    defaultSize: '1K',
  },
  {
    id: 'gpt-image-1.5-gen',
    name: 'gpt-image-1.5 (生图)',
    provider: 'lingy',
    tag: '生图',
    disabled: true,
    desc: 'GPT-image-1.5 生成速度提升 4 倍，支持精准局部编辑且保持光线构图一致性，文字渲染能力大幅增强。',
    supportedRatios: ['1:1', '16:9', '9:16'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: '1:1',
    defaultSize: '1K',
  },
  {
    id: 'gpt-image-1.5-edit',
    name: 'gpt-image-1.5 (修图)',
    provider: 'lingy',
    tag: '修图',
    disabled: true,
    desc: 'GPT-image-1.5 修图模式，支持精准局部编辑且保持光线构图一致性，文字渲染能力大幅增强。',
    supportedRatios: ['auto'],
    supportedSizes: ['1K', '2K'],
    supportsSearch: false,
    defaultRatio: 'auto',
    defaultSize: '1K',
  },
  {
    id: 'rmbg-2.0',
    name: 'RMBG-2.0 (背景移除)',
    provider: 'lingy',
    tag: '背景移除',
    disabled: false,
    desc: '背景移除模型，在精度和通用性上达到当前领先水平（SOTA），尤其在对复杂边缘（如发丝、透明物体）的处理上表现突出。',
    supportedRatios: ['auto'],
    supportedSizes: ['1K'],
    supportsSearch: false,
    defaultRatio: 'auto',
    defaultSize: '1K',
  },

  // ── 云雾AI 模型 ──────────────────────────────────────────────────────────────
  {
    id: 'gemini-2.5-flash-image',
    name: 'Gemini 2.5 Flash Image (生图)',
    provider: 'yunwu',
    tag: '生图',
    disabled: false,
    desc: 'Google Gemini 2.5 Flash 图像生成模型，速度极快，人物一致性强，光影逻辑合理，照片级逼真。支持联网检索获取实时信息。',
    supportedRatios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'],
    supportedSizes: ['1K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'gemini-2.5-flash-image-preview',
    name: 'Gemini 2.5 Flash Image Preview (生图)',
    provider: 'yunwu',
    tag: '生图',
    disabled: false,
    desc: 'Google Gemini 2.5 Flash Image 预览版，提前体验最新图像生成能力。速度极快，人物一致性强，支持联网检索。',
    supportedRatios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'],
    supportedSizes: ['1K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'gemini-3-pro-image-preview',
    name: 'Gemini 3 Pro Image Preview (生图)',
    provider: 'yunwu',
    tag: '生图',
    disabled: false,
    desc: 'Google Gemini 3 Pro 图像生成预览版，旗舰级专业图像质量。支持高分辨率输出，具备工作室级细节处理能力，可连接 Google 搜索实时数据。',
    supportedRatios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'],
    supportedSizes: ['1K', '2K', '4K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
  {
    id: 'gemini-3.1-flash-image-preview',
    name: 'Gemini 3.1 Flash Image Preview (生图)',
    provider: 'yunwu',
    tag: '生图',
    disabled: false,
    desc: 'Google Gemini 3.1 Flash Image 预览版，新一代极速图像生成模型。支持超宽/超竖等极端比例，支持 0.5K 超小尺寸及 4K 超高清输出，支持联网检索。',
    supportedRatios: ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9', '1:4', '4:1', '1:8', '8:1'],
    supportedSizes: ['512', '1K', '2K', '4K'],
    supportsSearch: true,
    defaultRatio: '3:4',
    defaultSize: '1K',
  },
]

// ─── 视频模型配置 ──────────────────────────────────────────────────────────────

export const VIDEO_RATIO_OPTIONS = [
  { label: '16:9 (横屏)', value: '16:9' },
  { label: '9:16 (竖屏)', value: '9:16' },
  { label: '1:1 (方形)', value: '1:1' },
]

export const VIDEO_DURATION_OPTIONS = [
  { label: '5 秒', value: 5 },
  { label: '10 秒', value: 10 },
]

/** @type {Array<{id:string, name:string, desc:string, disabled:boolean}>} */
export const VIDEO_MODELS = [
  {
    id: 'stub-video',
    name: '视频生成（开发中）',
    desc: '视频生成功能正在接入中，敬请期待',
    disabled: true,
  },
]

// ─── 工具函数 ──────────────────────────────────────────────────────────────────

/** 按 id 查找图像模型配置，未找到时返回第一个 */
export function getImageModelById(id) {
  return IMAGE_MODELS.find(m => m.id === id) ?? IMAGE_MODELS[0]
}

/** 按供应商 id 过滤图像模型列表 */
export function getModelsByProvider(providerId) {
  return IMAGE_MODELS.filter(m => m.provider === providerId)
}

/** 通过模型 id 反查供应商 id */
export function getProviderIdByModelId(modelId) {
  return getImageModelById(modelId).provider ?? 'lingy'
}

/** 返回当前模型支持的比例选项列表 */
export function getAvailableRatios(modelId) {
  const model = getImageModelById(modelId)
  return RATIO_OPTIONS.filter(opt => model.supportedRatios.includes(opt.value))
}

/** 返回当前模型支持的分辨率选项列表 */
export function getAvailableSizes(modelId) {
  const model = getImageModelById(modelId)
  return SIZE_OPTIONS.filter(opt => model.supportedSizes.includes(opt.value))
}
