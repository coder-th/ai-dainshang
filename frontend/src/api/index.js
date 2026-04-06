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
   * @param {{
   *   api_key: string,
   *   model: string,
   *   prompt: string,
   *   ratio: string,
   *   duration: number
   * }} data
   */
  generate: (data) => generateHttp.post("/generate-video/", data),
};

