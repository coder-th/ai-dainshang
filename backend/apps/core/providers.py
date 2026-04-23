"""
AI Provider 抽象层

职责：
- 定义 BaseImageProvider / BaseVideoProvider 抽象基类
- 每个 Provider 封装：API URL、请求体构造、响应解析
- Provider 注册表：按 model_id 路由到对应 Provider 实例

新增 Provider 步骤：
1. 继承 BaseImageProvider 或 BaseVideoProvider
2. 声明 supported_models 和 provider_id
3. 实现 api_url、build_payload、parse_response
4. 将实例追加到 _IMAGE_PROVIDERS 或 _VIDEO_PROVIDERS
"""

from abc import ABC, abstractmethod


# ─── 图像生成 Provider ────────────────────────────────────────────────────────

class BaseImageProvider(ABC):
    """图像生成 Provider 基类"""

    supported_models: list = []

    # 供应商唯一标识，与前端 providers.js 中的 id 对应
    provider_id: str = ""

    @property
    @abstractmethod
    def api_url(self) -> str:
        """该 Provider 的请求 URL（部分 Provider 需要 model_id 动态拼接，可重写为方法）"""
        ...

    def get_api_url(self, model: str) -> str:
        """返回实际请求 URL，默认直接返回 api_url 属性（可按需重写）"""
        return self.api_url

    @abstractmethod
    def build_payload(
        self,
        model: str,
        prompt: str,
        image_size: str,
        search: bool,
        aspect_ratio: str | None,
        base_images: list,
        ref_images: list,
    ) -> dict:
        """将前端参数转换为该 Provider 的 HTTP 请求 body"""
        ...

    @abstractmethod
    def parse_response(self, data: dict) -> str:
        """从 Provider 原始响应中提取图片 URL"""
        ...

    def get_request_headers(self, api_key: str) -> dict:
        """返回该 Provider 所需的请求 Headers，默认 Bearer Token 认证"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_request_kwargs(self, api_key: str, payload: dict, model: str) -> dict:
        """
        返回 requests.post 的完整 kwargs（url、headers、json、params 等）。
        大多数 Provider 只需重写 get_request_headers；
        如有 Query 参数等特殊需求可重写此方法。
        """
        return {
            "url": self.get_api_url(model),
            "json": payload,
            "headers": self.get_request_headers(api_key),
        }


class LingyaImageProvider(BaseImageProvider):
    """
    灵芽AI 图像生成 Provider
    文档：https://api.lingyaai.cn
    """

    provider_id = "lingy"

    supported_models = [
        "nano-banana-2",
        "nano-banana-pro",
        "nano-banana",
        "seedream-5.0",
        "seedream-4.5",
        "z-image-turbo",
        "qwen-image-max",
        "qwen-image-edit-max",
        "gpt-image-1.5-gen",
        "gpt-image-1.5-edit",
        "rmbg-2.0",
    ]

    @property
    def api_url(self) -> str:
        return "https://api.lingyaai.cn/v1/images/generations"

    def build_payload(
        self, model, prompt, image_size, search,
        aspect_ratio, base_images, ref_images,
    ) -> dict:
        payload = {
            "model": model,
            "prompt": prompt,
            "image_size": image_size,
            "search": search,
        }
        if aspect_ratio and aspect_ratio != "auto":
            payload["aspect_ratio"] = aspect_ratio
        # 灵芽规范：image 列表 = [基准图, ...参考图]，无图片时不传（文生图模式）
        combined = [*base_images, *ref_images]
        if combined:
            payload["image"] = combined
        return payload

    def parse_response(self, data: dict) -> str:
        return data["data"][0]["url"]


def _strip_data_uri(b64_str: str) -> str:
    """
    移除 base64 字符串的 data URI 前缀（如 data:image/jpeg;base64,），
    云雾AI 接口仅接受纯 base64 字符串。
    使用 split(";base64,") 而非正则，兼容 MIME 带额外参数的格式。
    """
    if b64_str and ";base64," in b64_str:
        return b64_str.split(";base64,", 1)[1]
    return b64_str or ""


def _guess_mime(b64_str: str) -> str:
    """从 data URI 前缀猜测 MIME 类型，默认 image/jpeg"""
    if b64_str and b64_str.startswith("data:") and ";" in b64_str:
        return b64_str[5 : b64_str.index(";")]
    return "image/jpeg"


class YunwuImageProvider(BaseImageProvider):
    """
    云雾AI 图像生成 Provider（基于 Google Gemini API 格式）
    API 文档：https://yunwu.ai
    端点：https://yunwu.ai/v1beta/models/{modelName}:generateContent
    认证：Header Authorization: Bearer <api_key>
         Query  key=<api_key>
    """


    supported_models = [
        "gemini-2.5-flash-image",
        "gemini-2.5-flash-image-preview",
        "gemini-3-pro-image-preview",
        "gemini-3.1-flash-image-preview",
    ]

    _BASE_URL = "https://yunwu.ai/v1beta/models"

    @property
    def api_url(self) -> str:
        # 占位，实际 URL 通过 get_api_url(model) 动态生成
        return f"{self._BASE_URL}/gemini-2.5-flash-image:generateContent"

    def get_api_url(self, model: str,api_key: str) -> str:
        # return f"{self._BASE_URL}/{model}:generateContent"
        return f"{self._BASE_URL}/{model}:generateContent"

    def get_request_headers(self, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_request_kwargs(self, api_key: str, payload: dict, model: str) -> dict:
        return {
            "url": self.get_api_url(model,api_key),
            "json": payload,
            "headers": self.get_request_headers(api_key),
            "params": {"key": api_key},
        }

    def build_payload(
        self, model, prompt, image_size, search,
        aspect_ratio, base_images, ref_images,
    ) -> dict:
        """
        构建云雾AI（Gemini）格式的请求体。

        - 文生图（无基准图）：contents[0].parts = [{"text": prompt}]
        - 多图模式（有图片）：contents[0].parts = [{"text": prompt}, {"inline_data": ...}, ...]
          图片顺序：基准图在前，参考图在后
        """
        parts = [{"text": prompt}]

        all_images = [*base_images, *ref_images]
        for img_b64 in all_images:
            parts.append({
                "inline_data": {
                    "mime_type": _guess_mime(img_b64),
                    "data": _strip_data_uri(img_b64),
                }
            })

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {},
            },
        }

        image_config = payload["generationConfig"]["imageConfig"]

        if aspect_ratio and aspect_ratio != "auto":
            image_config["aspectRatio"] = aspect_ratio

        # imageSize：云雾AI接受 "1K"、"2K"、"4K"、"512"（0.5K）
        if image_size:
            image_config["imageSize"] = image_size

        return payload

    def parse_response(self, data: dict) -> str:
        """
        从云雾AI（Gemini）响应中提取生成图片的 base64 数据，
        返回 data URI 格式供前端直接使用。

        响应结构示例：
        {
            "candidates": [{
                "content": {
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": "<base64>"}}
                    ]
                }
            }]
        }
        """
        candidates = data.get("candidates", [])
        if not candidates:
            raise KeyError("云雾AI 响应中缺少 candidates 字段")

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline:
                mime = inline.get("mimeType", "image/jpeg")
                b64_data = inline.get("data", "")
                return f"data:{mime};base64,{b64_data}"

        raise KeyError("云雾AI 响应中未找到图片数据")


class YunwuGptImageProvider(BaseImageProvider):
    """
    云雾AI GPT 图像生成 Provider
    端点：POST https://yunwu.ai/v1/images/generations
    认证：Header Authorization: Bearer <api_key>
    支持文生图和图像编辑（最多 5 张参考图）
    """

    provider_id = "yunwu_gpt"

    supported_models = [
        "gpt-image-2-all",
        "gpt-image-2",
        "gpt-image-1",
    ]

    # GPT 图像支持的 size 规格映射：前端分辨率标识 → API size 字符串
    _SIZE_MAP = {
        "1K": "1024x1024",
        "2K": "1024x1024",  # GPT 图像不支持 2K，降级为 1024x1024
        "4K": "1024x1024",  # 同上
        "512": "1024x1024",
    }

    # 比例 → size 映射（GPT 图像通过 size 指定横竖版）
    _RATIO_TO_SIZE = {
        "16:9": "1536x1024",  # 横版
        "3:2":  "1536x1024",
        "4:3":  "1536x1024",
        "9:16": "1024x1536",  # 竖版
        "2:3":  "1024x1536",
        "3:4":  "1024x1536",
        "1:1":  "1024x1024",
        "auto": "1024x1024",
    }

    @property
    def api_url(self) -> str:
        return "https://yunwu.ai/v1/images/generations"

    def build_payload(
        self, model, prompt, image_size, search,
        aspect_ratio, base_images, ref_images, n: int = 1,
    ) -> dict:
        # 根据比例选择 size；比例未指定时用 image_size 映射
        if aspect_ratio and aspect_ratio != "auto":
            size = self._RATIO_TO_SIZE.get(aspect_ratio, "1024x1024")
        else:
            size = self._SIZE_MAP.get(image_size, "1024x1024")

        _ = search  # GPT 图像 API 不支持联网检索，保留参数仅为统一签名

        payload: dict = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": max(1, min(int(n or 1), 10)),
        }

        # 图像编辑模式：传入参考图（最多 5 张），base64 data URI 格式
        images = [*base_images, *ref_images]
        if images:
            payload["image"] = images[:5]  # API 上限 5 张

        return payload

    def parse_response(self, data: dict) -> list[str]:
        """返回所有生成图片的 URL 列表（兼容 n>1 的多图输出）"""
        items = data.get("data", [])
        if not items:
            raise KeyError("GPT 图像响应中缺少 data 字段")
        urls = []
        for item in items:
            if item.get("url"):
                urls.append(item["url"])
            elif item.get("b64_json"):
                urls.append(f"data:image/png;base64,{item['b64_json']}")
        if not urls:
            raise KeyError("GPT 图像响应中未找到 url 或 b64_json 字段")
        return urls


# ─── 视频生成 Provider ────────────────────────────────────────────────────────

class BaseVideoProvider(ABC):
    """视频生成 Provider 基类"""

    supported_models: list = []

    @property
    @abstractmethod
    def api_url(self) -> str:
        ...

    @abstractmethod
    def build_payload(self, model: str, prompt: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def parse_response(self, data: dict) -> dict:
        """
        返回规范化结果，格式：
        {"type": "url", "value": "https://..."}  直接返回视频 URL
        {"type": "task_id", "value": "xxx"}      异步任务需轮询
        """
        ...

    def get_request_headers(self, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_request_kwargs(self, api_key: str, payload: dict, model: str) -> dict:
        return {
            "url": self.api_url,
            "json": payload,
            "headers": self.get_request_headers(api_key),
        }


class YunwuVeoVideoProvider(BaseVideoProvider):
    """
    云雾AI Veo 视频生成 Provider
    提交端点：POST https://yunwu.ai/v1/video/create
    任务查询：GET  https://yunwu.ai/v1/video/query?task_id={task_id}
    """

    provider_id = "yunwu"

    supported_models = [
        "veo2", "veo2-fast", "veo2-fast-frames", "veo2-fast-components",
        "veo2-pro", "veo2-pro-components",
        "veo3", "veo3-fast", "veo3-fast-frames", "veo3-frames",
        "veo3-pro", "veo3-pro-frames",
        "veo3.1", "veo3.1-fast", "veo3.1-pro",
        "veo3.1-4k", "veo3.1-pro-4k",
    ]

    _BASE_URL = "https://yunwu.ai"

    @property
    def api_url(self) -> str:
        return f"{self._BASE_URL}/v1/video/create"

    @property
    def _task_query_url(self) -> str:
        return f"{self._BASE_URL}/v1/video/query"

    def build_payload(self, model: str, prompt: str, **kwargs) -> dict:
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "enable_upsample": True,
            "enhance_prompt": True,
        }

        # 图片参数：去除 data URI 前缀，传纯 base64
        images: list = kwargs.get("images") or []
        if images:
            # payload["images"] = [_strip_data_uri(img) for img in images]
            payload["images"] = images

        # 视频比例：仅 veo3 系列支持（"16:9" 或 "9:16"）
        aspect_ratio: str | None = kwargs.get("aspect_ratio")
        if aspect_ratio and model.startswith("veo3"):
            payload["aspect_ratio"] = aspect_ratio

        # 时长（秒）
        duration = kwargs.get("duration")
        if duration is not None:
            payload["duration"] = int(duration)

        return payload

    def parse_response(self, data: dict) -> dict:
        # 异步任务：返回 task_id
        task_id = data.get("task_id") or data.get("id")
        if task_id:
            return {"type": "task_id", "value": str(task_id)}
        # 同步直接返回视频 URL
        url = data.get("url") or data.get("video_url")
        if url:
            return {"type": "url", "value": url}
        raise KeyError(f"无法解析视频生成响应，字段: {list(data.keys())}")

    def query_task(self, api_key: str, task_id: str) -> dict:
        """
        查询异步视频任务状态。
        返回规范化结果：
          {"status": "pending", "raw_status": "video_generating", "status_text": "视频生成中…"}
          {"status": "done", "video_url": "...", "enhanced_prompt": "...", ...}
          {"status": "error", "error": "...", ...}
        """
        _STATUS_TEXT = {
            "pending":                    "等待处理中…",
            "image_downloading":          "下载参考图片中…",
            "video_generating":           "视频生成中…",
            "video_generation_completed": "视频生成完成，超分辨率优化中…",
            "video_generation_failed":    "视频生成失败",
            "video_upsampling":           "超分辨率优化中…",
            "video_upsampling_completed": "超分优化完成，收尾处理中…",
            "video_upsampling_failed":    "超分辨率优化失败",
            "completed":                  "视频生成完成！",
            "failed":                     "任务失败",
            "error":                      "发生错误",
        }
        _TERMINAL_SUCCESS = {"completed"}
        _TERMINAL_FAILURE = {"failed", "error", "video_generation_failed", "video_upsampling_failed"}

        import requests as req
        headers = self.get_request_headers(api_key)
        resp = req.get(
            self._task_query_url,
            headers=headers,
            params={"id": task_id},   # 注意：参数名是 "id" 而非 "task_id"
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_status  = (data.get("status") or "").lower()
        status_text = _STATUS_TEXT.get(raw_status, f"状态: {raw_status}")
        base = {"raw_status": raw_status, "status_text": status_text}

        if raw_status in _TERMINAL_SUCCESS:
            return {**base, "status": "done",
                    "video_url": data.get("video_url"),
                    "enhanced_prompt": data.get("enhanced_prompt", "")}
        if raw_status in _TERMINAL_FAILURE:
            err_msg = data.get("error") or data.get("message") or status_text
            return {**base, "status": "error", "error": str(err_msg)}
        return {**base, "status": "pending"}


class LingyVideoProvider(BaseVideoProvider):
    """
    灵芽AI Veo 视频生成 Provider
    提交端点：POST https://api.lingyaai.cn/v1/videos  (multipart/form-data)
    任务查询：GET  https://api.lingyaai.cn/v1/videos/{id}

    size 参数格式：宽x高，如 16x9（横屏）、9x16（竖屏）
    图片参考：multipart input_reference 字段，首帧第 1 张，尾帧第 2 张
    """

    provider_id = "lingy_video"

    supported_models = [
        "veo_3_1-fast",
        "veo_3_1",
        "veo_3_1-fast-4K",
        "veo_3_1-4K",
    ]

    _BASE_URL = "https://api.lingyaai.cn"

    @property
    def api_url(self) -> str:
        return f"{self._BASE_URL}/v1/videos"

    def get_request_headers(self, api_key: str) -> dict:
        # 不设 Content-Type，由 requests 自动附加 multipart boundary
        return {"Authorization": f"Bearer {api_key}"}

    def build_payload(self, model: str, prompt: str, **kwargs) -> dict:
        payload: dict = {
            "prompt": prompt,
            "model": model,
        }
        # aspect_ratio "16:9" → size "16x9"
        aspect_ratio: str | None = kwargs.get("aspect_ratio")
        if aspect_ratio:
            payload["size"] = aspect_ratio.replace(":", "x")

        # 图片列表暂存（get_request_kwargs 取用后构造 multipart files）
        payload["_images"] = kwargs.get("images") or []
        return payload

    def get_request_kwargs(self, api_key: str, payload: dict, model: str = "") -> dict:  # noqa: ARG002
        import base64

        images = payload.get("_images") or []

        # 全部字段走 multipart（text 字段用 (None, value) 元组），确保 Content-Type 为 multipart/form-data
        multipart: list = []
        for k, v in payload.items():
            if k == "_images":
                continue
            if v is not None:
                multipart.append((k, (None, str(v))))

        # 图片字段：base64 data URI → bytes；URL → 直接传字符串
        for img in images:
            if not img:
                continue
            if ";base64," in img:
                mime = img[5:img.index(";")] if img.startswith("data:") else "image/jpeg"
                b64_data = img.split(";base64,", 1)[1]
                img_bytes = base64.b64decode(b64_data)
                ext = mime.split("/")[-1]
                multipart.append(("input_reference", (f"image.{ext}", img_bytes, mime)))
            elif img.startswith("http://") or img.startswith("https://"):
                multipart.append(("input_reference", (None, img)))

        return {
            "url": self.api_url,
            "files": multipart,
            "headers": self.get_request_headers(api_key),
        }

    def parse_response(self, data: dict) -> dict:
        task_id = data.get("id")
        if task_id:
            return {"type": "task_id", "value": str(task_id)}
        raise KeyError(f"灵芽AI视频响应中未找到任务 ID，字段: {list(data.keys())}")

    def query_task(self, api_key: str, task_id: str) -> dict:
        """
        查询灵芽AI异步视频任务状态。
        返回规范化结果：
          {"status": "pending", "status_text": "..."}
          {"status": "done",    "video_url": "...", "enhanced_prompt": ""}
          {"status": "error",   "error": "..."}

        灵芽AI 响应字段：
          id, object, model, status, progress(0-100), created_at,
          completed_at, expires_at, size, seconds, video_url, error
        """
        _STATUS_TEXT = {
            "queued":     "排队等待中…",
            "processing": "视频生成中…",
            "completed":  "视频生成完成！",
            "failed":     "任务失败",
        }
        _TERMINAL_SUCCESS = {"completed"}
        _TERMINAL_FAILURE = {"failed"}

        import requests as req
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = req.get(
            f"{self._BASE_URL}/v1/videos/{task_id}",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_status = (data.get("status") or "").lower()
        progress   = data.get("progress")  # 0-100，completed 时为 100

        base_text  = _STATUS_TEXT.get(raw_status, f"状态: {raw_status}")
        # 对 pending 状态附加进度百分比（如果有）
        if progress is not None and raw_status not in _TERMINAL_SUCCESS | _TERMINAL_FAILURE:
            status_text = f"{base_text}（{progress}%）"
        else:
            status_text = base_text

        base = {"raw_status": raw_status, "status_text": status_text}

        if raw_status in _TERMINAL_SUCCESS:
            return {
                **base,
                "status":          "done",
                "video_url":       data.get("video_url"),
                "enhanced_prompt": "",
            }

        if raw_status in _TERMINAL_FAILURE:
            err_msg = data.get("error") or data.get("message") or status_text
            return {**base, "status": "error", "error": str(err_msg)}

        return {**base, "status": "pending"}


# ─── Provider 注册表 ──────────────────────────────────────────────────────────

_IMAGE_PROVIDERS: list[BaseImageProvider] = [
    LingyaImageProvider(),
    YunwuImageProvider(),
    YunwuGptImageProvider(),
    # 新增其他 Provider 实例追加于此
]

_VIDEO_PROVIDERS: list[BaseVideoProvider] = [
    LingyVideoProvider(),
    YunwuVeoVideoProvider(),
    # 新增视频 Provider 追加于此
]


def get_image_provider(model_id: str, provider_id: str | None = None) -> BaseImageProvider:
    """
    根据 provider_id 或 model_id 返回对应的图像 Provider。

    优先使用 provider_id（前端明确指定的供应商），
    provider_id 未传时按 model_id 匹配 supported_models，
    两者都未匹配时回落到灵芽AI（首个 Provider）。
    """
    if provider_id:
        for provider in _IMAGE_PROVIDERS:
            if provider.provider_id == provider_id:
                return provider

    for provider in _IMAGE_PROVIDERS:
        if model_id in provider.supported_models:
            return provider

    return _IMAGE_PROVIDERS[0]


def get_video_provider(model_id: str) -> BaseVideoProvider:
    """根据 model_id 返回对应的视频 Provider"""
    for provider in _VIDEO_PROVIDERS:
        if model_id in provider.supported_models:
            return provider
    return _VIDEO_PROVIDERS[0]
