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


def _truncate_b64(value, max_len: int = 64) -> str:
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + f"...[{len(value)} chars]"
    return value


def _sanitize_payload(payload: dict) -> dict:
    result = dict(payload)
    if "image" in result:
        result["image"] = [_truncate_b64(img) for img in result["image"]]
    return result


# ─── 通用 HTTP 执行层 ─────────────────────────────────────────────────────────

def _call_provider(api_key: str, payload: dict, provider) -> str:
    """
    通用 HTTP 执行层：负责日志、超时、错误处理。
    URL 和响应解析由 provider 提供，实现 Provider 间解耦。
    """
    url = provider.api_url
    model = payload.get("model", "")
    logger.info("→ POST %s  model=%s  image_size=%s", url, model, payload.get("image_size"))
    t0 = time.monotonic()

    log_record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "provider": type(provider).__name__,
        "url": url,
        "request": _sanitize_payload(payload),
        "response": None,
        "error": None,
        "elapsed_s": None,
    }

    try:
        resp = req.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=180,
        )
        elapsed = time.monotonic() - t0
        logger.info("← %s %s  elapsed=%.2fs", resp.status_code, url, elapsed)
        resp.raise_for_status()
        data = resp.json()

        log_record["elapsed_s"] = round(elapsed, 3)
        log_record["response"] = {
            "status_code": resp.status_code,
            "keys": list(data.keys()),
            "data": _truncate_b64(str(data.get("data", [])), max_len=12800),
        }
        _write_api_log(log_record)

        return provider.parse_response(data)

    except req.Timeout:
        elapsed = time.monotonic() - t0
        logger.warning("✗ TIMEOUT %s  elapsed=%.2fs", url, elapsed)
        log_record["elapsed_s"] = round(elapsed, 3)
        log_record["error"] = "Timeout"
        _write_api_log(log_record)
        raise
    except req.HTTPError as e:
        elapsed = time.monotonic() - t0
        status_code = e.response.status_code if e.response is not None else None
        logger.error("✗ HTTP ERROR %s  status=%s  elapsed=%.2fs  detail=%s", url, status_code or "?", elapsed, e)
        log_record["elapsed_s"] = round(elapsed, 3)
        log_record["error"] = {"type": "HTTPError", "status_code": status_code, "detail": str(e)}
        _write_api_log(log_record)
        raise
    except req.RequestException as e:
        elapsed = time.monotonic() - t0
        logger.error("✗ REQUEST ERROR %s  elapsed=%.2fs  detail=%s", url, elapsed, e)
        log_record["elapsed_s"] = round(elapsed, 3)
        log_record["error"] = {"type": type(e).__name__, "detail": str(e)}
        _write_api_log(log_record)
        raise


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
        "model":        "nano-banana-2",
        "prompt":       "...",
        "aspect_ratio": "3:4",    // 可选，"auto" 时省略
        "image_size":   "1K",
        "search":       true,     // 可选，默认 false
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
        if not base_images:
            return Response({"error": "请至少上传一张基准图片"}, status=400)

        provider = get_image_provider(model)

        def run_task(idx_img):
            idx, base_img = idx_img
            try:
                payload = provider.build_payload(
                    model=model,
                    prompt=prompt,
                    image_size=image_size,
                    search=search,
                    aspect_ratio=aspect_ratio,
                    base_images=[base_img],
                    ref_images=ref_images,
                )
                url = _call_provider(api_key, payload, provider)
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
            except (KeyError, IndexError):
                return {"index": idx, "url": None, "error": "API 响应格式异常"}

        tasks = list(enumerate(base_images))
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
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        image_url = request.query_params.get("url", "").strip()
        if not image_url:
            return HttpResponseBadRequest("缺少 url 参数")

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
