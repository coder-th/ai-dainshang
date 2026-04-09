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


class StubVideoProvider(BaseVideoProvider):
    """视频生成占位 Provider（TODO: 接入真实服务）"""

    supported_models = ["stub-video"]

    @property
    def api_url(self) -> str:
        return ""  # TODO: 接入后填写

    def build_payload(self, model: str, prompt: str, **kwargs) -> dict:
        raise NotImplementedError("视频生成接口尚未实现")

    def parse_response(self, data: dict) -> dict:
        raise NotImplementedError("视频生成接口尚未实现")


# ─── Provider 注册表 ──────────────────────────────────────────────────────────

_IMAGE_PROVIDERS: list[BaseImageProvider] = [
    LingyaImageProvider(),
    YunwuImageProvider(),
    # 新增其他 Provider 实例追加于此
]

_VIDEO_PROVIDERS: list[BaseVideoProvider] = [
    StubVideoProvider(),
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
