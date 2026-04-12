import axios from "axios";

// 自动适配：生产环境（打包后）使用当前域名，开发时走 Vite proxy
const baseURL =
  import.meta.env.DEV ? "/api" : `${window.location.origin}/api`;

const http = axios.create({
  baseURL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// 图像生成专用实例（超时延长至 200s）
const generateHttp = axios.create({
  baseURL,
  timeout: 200000,
  headers: { "Content-Type": "application/json" },
});

// 响应拦截：统一错误提示
const errorInterceptor = (err) => {
  console.error("[API Error]", err.response?.data || err.message);
  return Promise.reject(err);
};
http.interceptors.response.use((res) => res, errorInterceptor);
generateHttp.interceptors.response.use((res) => res, errorInterceptor);

// ─── Item API ─────────────────────────────────────────────────────────────────
export const itemApi = {
  list: (params) => http.get("/items/", { params }),
  getStats: () => http.get("/items/stats/"),
  create: (data) => http.post("/items/", data),
  update: (id, data) => http.put(`/items/${id}/`, data),
  delete: (id) => http.delete(`/items/${id}/`),
};

// ─── Generate API ─────────────────────────────────────────────────────────────
export const generateApi = {
  /**
   * @param {{
   *   api_key: string,
   *   model: string,
   *   prompt: string,
   *   aspect_ratio: string,
   *   image_size: string,
   *   search: boolean,
   *   base_images: string[],
   *   ref_images: string[]
   * }} data
   */
  generate: (data) => generateHttp.post("/generate/", data),
};

// ─── Video API ────────────────────────────────────────────────────────────────
export const videoApi = {
  /**
   * 提交视频生成任务
   * @param {{
   *   api_key: string,
   *   model: string,
   *   prompt: string,
   *   images?: string[],
   *   aspect_ratio?: string,
   *   duration?: number
   * }} data
   */
  generate: (data) => generateHttp.post("/generate-video/", data),

  /**
   * 查询视频任务状态
   * @param {{ task_id: string, api_key: string, model: string }} params
   */
  queryTask: (params) => http.get("/video-task/", { params }),
};

// ─── Settings API ─────────────────────────────────────────────────────────────
export const settingsApi = {
  /** 读取配置项，返回 { key, value } */
  get: (key)         => http.get(`/settings/${key}/`),
  /** 保存配置项 */
  set: (key, value)  => http.put(`/settings/${key}/`, { value }),
  /** 删除配置项（恢复默认）*/
  del: (key)         => http.delete(`/settings/${key}/`),
};

// ─── Video History API ────────────────────────────────────────────────────────
export const historyApi = {
  /** 获取最近 30 天的视频历史（降序）*/
  list: ()       => http.get("/video-history/"),

  /** 新建一条历史记录 */
  create: (data) => http.post("/video-history/", data),

  /** 删除单条历史记录 */
  delete: (id)   => http.delete(`/video-history/${id}/`),

  /** 清空所有历史记录 */
  clearAll: ()   => http.delete("/video-history/clear/"),
};

// ─── Image History API ────────────────────────────────────────────────────────
export const imageHistoryApi = {
  /** 获取最近 30 天的图片历史（降序）*/
  list: ()       => http.get("/image-history/"),

  /** 新建一条历史记录 */
  create: (data) => http.post("/image-history/", data),

  /** 删除单条历史记录 */
  delete: (id)   => http.delete(`/image-history/${id}/`),

  /** 清空所有历史记录 */
  clearAll: ()   => http.delete("/image-history/clear/"),
};

