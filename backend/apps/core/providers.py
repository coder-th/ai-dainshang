"""
AI Provider 抽象层

职责：
- 定义 BaseImageProvider / BaseVideoProvider 抽象基类
- 每个 Provider 封装：API URL、请求体构造、响应解析
- Provider 注册表：按 model_id 路由到对应 Provider 实例

新增 Provider 步骤：
1. 继承 BaseImageProvider 或 BaseVideoProvider
2. 声明 supported_models
3. 实现 api_url、build_payload、parse_response
4. 将实例追加到 _IMAGE_PROVIDERS 或 _VIDEO_PROVIDERS
"""

from abc import ABC, abstractmethod


# ─── 图像生成 Provider ────────────────────────────────────────────────────────

class BaseImageProvider(ABC):
    """图像生成 Provider 基类"""

    supported_models: list = []

    @property
    @abstractmethod
    def api_url(self) -> str:
        """该 Provider 的请求 URL"""
        ...

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


class LingyaImageProvider(BaseImageProvider):
    """
    灵芽AI 图像生成 Provider
    文档：https://api.lingyaai.cn
    """

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
            # 灵芽规范：image 列表 = [基准图, ...参考图]
            "image": [*base_images, *ref_images],
        }
        if aspect_ratio and aspect_ratio != "auto":
            payload["aspect_ratio"] = aspect_ratio
        return payload

    def parse_response(self, data: dict) -> str:
        return data["data"][0]["url"]


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

_IMAGE_PROVIDERS: list = [
    LingyaImageProvider(),
    # 新增其他 Provider 实例追加于此
]

_VIDEO_PROVIDERS: list = [
    StubVideoProvider(),
    # 新增视频 Provider 追加于此
]


def get_image_provider(model_id: str) -> BaseImageProvider:
    """根据 model_id 返回对应的图像 Provider，未匹配时回落到灵芽AI"""
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
