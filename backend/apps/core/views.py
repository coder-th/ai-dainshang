import concurrent.futures
import json
import logging
import os
import time
from datetime import datetime

import requests as req
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item
from .serializers import ItemSerializer
from .providers import get_image_provider

logger = logging.getLogger("outbound")

# ─── API 调用日志 ─────────────────────────────────────────────────────────────

_API_LOG_DIR = os.path.join(getattr(settings, "LOGS_DIR", "logs"), "api-calls")
os.makedirs(_API_LOG_DIR, exist_ok=True)


def _write_api_log(record: dict) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(_API_LOG_DIR, f"{date_str}.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _clip(text, n: int = 1000) -> str:
    """截断过长字符串，防止日志膨胀"""
    s = text if isinstance(text, str) else str(text)
    return s if len(s) <= n else s[:n] + f"...[{len(s)} chars]"


# ─── 通用 HTTP 执行层 ─────────────────────────────────────────────────────────

def _call_provider(api_key: str, payload: dict, provider, model: str = "") -> str:
    """
    通用 HTTP 执行层：负责日志、超时、错误处理。
    URL 和响应解析由 provider 提供，实现 Provider 间解耦。
    """
    request_kwargs = provider.get_request_kwargs(api_key, payload, model)
    url = request_kwargs["url"]

    # 最小化初始字段，确保 finally 块中 log_record 始终有效
    log_record: dict = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "provider": type(provider).__name__,
        "url": url,
        "model": model,
        "request": None,
        "response": None,
        "error": None,
        "elapsed_s": None,
    }

    # 记录请求摘要到 outbound.log（含认证方式，便于调试）
    has_bearer = bool(request_kwargs.get("headers", {}).get("Authorization"))
    has_key    = "key" in request_kwargs.get("params", {})
    logger.info(
        "→ POST %s  provider=%s  model=%s  auth=[bearer=%s key_param=%s]",
        url, type(provider).__name__, model, has_bearer, has_key,
    )
    t0 = time.monotonic()

    try:
        # 序列化请求体（独立 try，失败不影响整体日志写入）
        try:
            log_record["request"] = _clip(json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            log_record["request"] = f"[serialize error: {e}]"

        post_kwargs = dict(request_kwargs)
        post_url = post_kwargs.pop("url")
        resp = req.post(post_url, timeout=180, **post_kwargs)
        elapsed = time.monotonic() - t0
        log_record["elapsed_s"] = round(elapsed, 3)
        logger.info("← %s  elapsed=%.2fs  url=%s", resp.status_code, elapsed, url)

        log_record["response"] = {
            "status_code": resp.status_code,
            "body": _clip(resp.text, 2000),
        }

        resp.raise_for_status()
        data = resp.json()
        result_url = provider.parse_response(data)
        return result_url

    except req.Timeout:
        elapsed = time.monotonic() - t0
        log_record["elapsed_s"] = round(elapsed, 3)
        log_record["error"] = "Timeout"
        logger.warning("✗ TIMEOUT %s  elapsed=%.2fs", url, elapsed)
        raise
    except req.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else None
        err_detail = e.response.text[:500] if e.response is not None else str(e)
        log_record["error"] = {"status_code": status_code, "detail": err_detail}
        logger.error("✗ HTTP ERROR %s  status=%s  detail=%s", url, status_code, err_detail)
        raise
    except Exception as e:
        log_record["error"] = {"type": type(e).__name__, "detail": str(e)}
        logger.error("✗ ERROR %s  %s: %s", url, type(e).__name__, e)
        raise
    finally:
        try:
            _write_api_log(log_record)
        except Exception as e:
            logger.error("✗ 日志写入失败: %s", e)


# ─── Item CRUD ────────────────────────────────────────────────────────────────

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        total = Item.objects.count()
        active = Item.objects.filter(status="active").count()
        return Response({"total": total, "active": active, "inactive": total - active})


# ─── 图像生成 ─────────────────────────────────────────────────────────────────

class GenerateView(APIView):
    """
    POST /api/generate/

    请求体：
    {
        "api_key":      "sk-...",
        "provider":     "lingy",          // 可选，供应商 id（lingy / yunwu）
        "model":        "nano-banana-2",
        "prompt":       "...",
        "aspect_ratio": "3:4",            // 可选，"auto" 时省略
        "image_size":   "1K",
        "search":       true,             // 可选，默认 false
        "base_images":  ["data:image/jpeg;base64,..."],
        "ref_images":   ["data:image/jpeg;base64,..."]
    }

    响应体：
    {
        "results": [
            {"index": 0, "url": "https://...", "error": null},
            {"index": 1, "url": null, "error": "超时"}
        ]
    }
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        d = request.data
        api_key = (d.get("api_key") or "").strip()
        provider_id = (d.get("provider") or "").strip() or None
        model = d.get("model") or "nano-banana-2"
        prompt = (d.get("prompt") or "").strip()
        aspect_ratio = d.get("aspect_ratio") or "auto"
        image_size = d.get("image_size") or "1K"
        search = bool(d.get("search", False))
        base_images = d.get("base_images") or []
        ref_images = d.get("ref_images") or []

        if not api_key:
            return Response({"error": "缺少 API 密钥"}, status=400)
        if not prompt:
            return Response({"error": "缺少创意描述"}, status=400)

        # 没有基准图时切换为文生图模式
        is_text_to_image = len(base_images) == 0

        # provider_id 优先，未传则按 model_id 匹配
        provider = get_image_provider(model, provider_id=provider_id)

        def run_task(idx_img):
            idx, base_img = idx_img
            try:
                payload = provider.build_payload(
                    model=model,
                    prompt=prompt,
                    image_size=image_size,
                    search=search,
                    aspect_ratio=aspect_ratio,
                    base_images=[] if is_text_to_image else [base_img],
                    ref_images=[] if is_text_to_image else ref_images,
                )
                url = _call_provider(api_key, payload, provider, model=model)
                return {"index": idx, "url": url, "error": None}
            except req.Timeout:
                return {"index": idx, "url": None, "error": "请求超时，请重试"}
            except req.HTTPError as e:
                try:
                    msg = e.response.json().get("error", {}).get("message", str(e))
                except Exception:
                    msg = str(e)
                return {"index": idx, "url": None, "error": f"API 错误: {msg}"}
            except req.RequestException as e:
                return {"index": idx, "url": None, "error": f"网络错误: {str(e)}"}
            except (KeyError, IndexError) as e:
                return {"index": idx, "url": None, "error": f"API 响应格式异常: {str(e)}"}

        # 文生图模式：创建单个虚拟任务（index=0，无基准图）
        tasks = [(0, None)] if is_text_to_image else list(enumerate(base_images))
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            results = list(pool.map(run_task, tasks))

        results.sort(key=lambda r: r["index"])
        return Response({"results": results})


# ─── 视频生成（骨架） ─────────────────────────────────────────────────────────

class VideoGenerateView(APIView):
    """
    POST /api/generate-video/

    请求体：
    {
        "api_key":  "sk-...",
        "model":    "stub-video",
        "prompt":   "...",
        "duration": 5,        // 秒，可选
        "ratio":    "16:9"    // 可选
    }

    响应体（异步任务型 Provider）：
    {"task_id": "xxx", "status": "pending"}

    响应体（直接返回 URL 型 Provider）：
    {"url": "https://..."}

    注：当前返回 501，等接入真实视频 Provider 后实现。
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # TODO: 接入视频生成 Provider 后实现
        return Response({"error": "视频生成功能开发中，敬请期待"}, status=501)


# ─── 图片代理下载 ─────────────────────────────────────────────────────────────

class ProxyImageView(APIView):
    """
    GET /api/proxy-image/?url=<远程图片URL>
    由服务端代下载远程图片并流式返回，解决前端直接 fetch 的 CORS 限制。
    支持 data URI（云雾AI 直接返回 base64 时）转发给前端。
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        image_url = request.query_params.get("url", "").strip()
        if not image_url:
            return HttpResponseBadRequest("缺少 url 参数")

        # 云雾AI 返回 data URI（base64），直接解码并返回
        if image_url.startswith("data:"):
            import base64
            try:
                header, b64_data = image_url.split(",", 1)
                mime = header.split(":")[1].split(";")[0]
                raw = base64.b64decode(b64_data)
                from django.http import HttpResponse
                response = HttpResponse(raw, content_type=mime)
                response["Content-Length"] = str(len(raw))
                response["Content-Disposition"] = 'attachment; filename="image.jpg"'
                return response
            except Exception as e:
                return HttpResponseBadRequest(f"data URI 解析失败: {e}")

        try:
            remote = req.get(image_url, stream=True, timeout=60)
            remote.raise_for_status()
        except req.RequestException as e:
            return HttpResponseBadRequest(f"图片获取失败: {e}")

        content_type = remote.headers.get("Content-Type", "image/jpeg")
        filename = image_url.split("/")[-1].split("?")[0] or "image.jpg"

        response = StreamingHttpResponse(
            remote.iter_content(chunk_size=8192),
            content_type=content_type,
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        if "Content-Length" in remote.headers:
            response["Content-Length"] = remote.headers["Content-Length"]
        return response
