import base64
import concurrent.futures
import json
import logging
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import requests as req
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponseBadRequest, FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item, VideoHistory, ImageHistory, Settings
from .serializers import ItemSerializer, VideoHistorySerializer, ImageHistorySerializer, SettingsSerializer
from .providers import get_image_provider, get_video_provider

logger = logging.getLogger("outbound")

# ─── 媒体文件目录 ──────────────────────────────────────────────────────────────

DATA_DIR = getattr(settings, "DATA_DIR", settings.BASE_DIR if hasattr(settings, "BASE_DIR") else ".")

# 默认回退目录（用户未配置导出路径时）
_DEFAULT_VIDEOS_DIR = os.path.join(DATA_DIR, "media", "videos")
_DEFAULT_IMAGES_DIR = os.path.join(DATA_DIR, "media", "images")
os.makedirs(_DEFAULT_VIDEOS_DIR, exist_ok=True)
os.makedirs(_DEFAULT_IMAGES_DIR, exist_ok=True)

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


# ─── 媒体文件自动下载工具 ─────────────────────────────────────────────────────

def _is_remote_url(url: str) -> bool:
    """判断是否为远程 http/https 链接"""
    return isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))


def _download_video(video_url: str, task_id: str = None, base_dir: str = None) -> str | None:
    """
    将远程视频下载到 {base_dir}/videos/{task_id}.mp4。
    base_dir 为用户配置的导出路径根目录，缺省时使用 DATA_DIR/media。
    task_id 缺失时使用时间戳。
    成功返回本地绝对路径，失败返回 None。
    """
    if not _is_remote_url(video_url):
        return None
    try:
        videos_dir = os.path.join(base_dir, "videos") if base_dir else _DEFAULT_VIDEOS_DIR
        os.makedirs(videos_dir, exist_ok=True)
        safe_name = (task_id or datetime.now().strftime("%Y%m%d%H%M%S%f")).replace("/", "_").replace(":", "_")
        # 从 URL 中尝试推断后缀
        parsed_path = urllib.parse.urlparse(video_url).path
        ext = os.path.splitext(parsed_path)[1].lower()
        if ext not in (".mp4", ".webm", ".mov", ".avi"):
            ext = ".mp4"
        filename = f"{safe_name}{ext}"
        local_path = os.path.join(videos_dir, filename)
        resp = req.get(video_url, stream=True, timeout=180)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        logger.info("✓ 视频已下载: %s → %s", video_url[:80], local_path)
        return local_path
    except Exception as e:
        logger.warning("✗ 视频下载失败 %s: %s", video_url[:80], e)
        return None



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


# ─── 系统配置 ─────────────────────────────────────────────────────────────────

class SettingsView(APIView):
    """
    GET  /api/settings/<key>/   → {"key": "...", "value": "..."}
    PUT  /api/settings/<key>/   → {"value": "..."}  保存或更新
    DELETE /api/settings/<key>/ → 删除（恢复默认）
    """

    authentication_classes = []
    permission_classes = []

    def get(self, _request, key):
        value = Settings.get(key)
        return Response({"key": key, "value": value})

    def put(self, request, key):
        value = request.data.get("value", "")
        Settings.set(key, value)
        return Response({"key": key, "value": value})

    def delete(self, _request, key):
        Settings.objects.filter(pk=key).delete()
        return Response(status=204)


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
        n_images = max(1, min(int(d.get("n_images") or 1), 10))

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
                    n=n_images,
                )
                raw = _call_provider(api_key, payload, provider, model=model)
                # parse_response 可能返回单个 URL（str）或多个 URL（list[str]）
                urls = raw if isinstance(raw, list) else [raw]
                return [{"index": idx * n_images + i, "url": u, "error": None} for i, u in enumerate(urls)]
            except req.Timeout:
                return [{"index": idx, "url": None, "error": "请求超时，请重试"}]
            except req.HTTPError as e:
                try:
                    msg = e.response.json().get("error", {}).get("message", str(e))
                except Exception:
                    msg = str(e)
                return [{"index": idx, "url": None, "error": f"API 错误: {msg}"}]
            except req.RequestException as e:
                return [{"index": idx, "url": None, "error": f"网络错误: {str(e)}"}]
            except (KeyError, IndexError) as e:
                return [{"index": idx, "url": None, "error": f"API 响应格式异常: {str(e)}"}]

        # 文生图模式：创建单个虚拟任务（index=0，无基准图）
        tasks = [(0, None)] if is_text_to_image else list(enumerate(base_images))
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            nested = list(pool.map(run_task, tasks))

        # 展平嵌套列表并按 index 排序
        results = [item for sublist in nested for item in sublist]
        results.sort(key=lambda r: r["index"])
        return Response({"results": results})


# ─── 视频生成 HTTP 执行层 ──────────────────────────────────────────────────────

def _call_video_provider(api_key: str, payload: dict, provider) -> dict:
    """
    视频生成提交层：负责日志、超时、错误处理。
    返回规范化结果 dict（同 BaseVideoProvider.parse_response 格式）。
    """
    request_kwargs = provider.get_request_kwargs(api_key, payload, payload.get("model", ""))
    url = request_kwargs["url"]
    model = payload.get("model", "")

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

    has_bearer = bool(request_kwargs.get("headers", {}).get("Authorization"))
    logger.info("→ POST %s  provider=%s  model=%s  auth=[bearer=%s]",
                url, type(provider).__name__, model, has_bearer)
    t0 = time.monotonic()

    try:
        try:
            log_record["request"] = _clip(json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            log_record["request"] = f"[serialize error: {e}]"

        post_kwargs = dict(request_kwargs)
        post_url = post_kwargs.pop("url")
        resp = req.post(post_url, timeout=60, **post_kwargs)
        elapsed = time.monotonic() - t0
        log_record["elapsed_s"] = round(elapsed, 3)
        logger.info("← %s  elapsed=%.2fs  url=%s", resp.status_code, elapsed, url)

        log_record["response"] = {
            "status_code": resp.status_code,
            "body": _clip(resp.text, 2000),
        }

        resp.raise_for_status()
        data = resp.json()
        return provider.parse_response(data)

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


# ─── 视频生成 ─────────────────────────────────────────────────────────────────

class VideoGenerateView(APIView):
    """
    POST /api/generate-video/

    请求体：
    {
        "api_key":      "sk-...",
        "model":        "veo3.1-fast",
        "prompt":       "...",
        "images":       ["data:image/jpeg;base64,..."],  // 可选
        "aspect_ratio": "16:9",                          // 可选，仅 veo3 系列
        "duration":     8                                // 可选，秒
    }

    响应体（异步任务）：{"task_id": "xxx", "status": "pending"}
    响应体（同步完成）：{"video_url": "https://...", "status": "done"}
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        d = request.data
        api_key = (d.get("api_key") or "").strip()
        model = (d.get("model") or "veo3.1-fast").strip()
        prompt = (d.get("prompt") or "").strip()
        aspect_ratio = d.get("aspect_ratio") or None
        duration = d.get("duration", 8)
        images = d.get("images") or []

        if not api_key:
            return Response({"error": "缺少 API 密钥"}, status=400)
        if not prompt:
            return Response({"error": "缺少视频描述"}, status=400)

        provider = get_video_provider(model)
        payload = provider.build_payload(
            model=model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            duration=duration,
            images=images,
        )

        try:
            result = _call_video_provider(api_key, payload, provider)
            if result["type"] == "task_id":
                return Response({"task_id": result["value"], "status": "pending"})
            else:
                return Response({"video_url": result["value"], "status": "done"})
        except req.Timeout:
            return Response({"error": "请求超时，请重试"}, status=504)
        except req.HTTPError as e:
            try:
                msg = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)
            return Response({"error": f"API 错误: {msg}"}, status=502)
        except req.RequestException as e:
            return Response({"error": f"网络错误: {str(e)}"}, status=502)
        except (KeyError, IndexError) as e:
            return Response({"error": f"API 响应格式异常: {str(e)}"}, status=502)
        except Exception as e:
            return Response({"error": f"服务器错误: {str(e)}"}, status=500)


# ─── 视频任务查询 ─────────────────────────────────────────────────────────────

class VideoTaskQueryView(APIView):
    """
    GET /api/video-task/?task_id=xxx&api_key=sk-...&model=veo3.1-fast

    响应体：
    {"status": "pending"}
    {"status": "done", "video_url": "https://..."}
    {"status": "error", "error": "..."}
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        task_id = request.query_params.get("task_id", "").strip()
        api_key = request.query_params.get("api_key", "").strip()
        model = request.query_params.get("model", "veo3.1-fast").strip()

        if not task_id:
            return Response({"error": "缺少 task_id"}, status=400)
        if not api_key:
            return Response({"error": "缺少 API 密钥"}, status=400)

        provider = get_video_provider(model)
        if not hasattr(provider, "query_task"):
            return Response({"error": "该 Provider 不支持任务查询"}, status=501)

        try:
            result = provider.query_task(api_key, task_id)
            return Response(result)
        except req.HTTPError as e:
            try:
                msg = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)
            return Response({"error": f"API 错误: {msg}"}, status=502)
        except req.RequestException as e:
            return Response({"error": f"网络错误: {str(e)}"}, status=502)
        except Exception as e:
            return Response({"error": f"查询失败: {str(e)}"}, status=500)


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


# ─── 本地媒体文件服务 ─────────────────────────────────────────────────────────

class MediaFileView(APIView):
    """
    通过数据库记录 ID 读取本地媒体文件，支持任意用户配置的保存目录。

    GET /api/media/video/?id=<video_history_id>
        → 返回该记录的 video_path 文件内容

    GET /api/media/image/?id=<image_history_id>&index=<result_index>
        → 返回该记录 results[index].path 文件内容
    """

    authentication_classes = []
    permission_classes = []

    _CONTENT_TYPES = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    def _serve_file(self, path: str):
        if not path or not os.path.isfile(path):
            raise Http404("文件不存在")
        ext = os.path.splitext(path)[1].lower()
        content_type = self._CONTENT_TYPES.get(ext, "application/octet-stream")
        return FileResponse(open(path, "rb"), content_type=content_type)

    def get(self, request, media_type=""):
        if media_type == "video":
            record_id = request.query_params.get("id", "").strip()
            if not record_id:
                return HttpResponseBadRequest("缺少 id 参数")
            try:
                record = VideoHistory.objects.only("video_path").get(pk=int(record_id))
            except (VideoHistory.DoesNotExist, ValueError):
                raise Http404("记录不存在")
            return self._serve_file(record.video_path)

        if media_type == "image":
            record_id = request.query_params.get("id", "").strip()
            index_str = request.query_params.get("index", "0").strip()
            if not record_id:
                return HttpResponseBadRequest("缺少 id 参数")
            try:
                record = ImageHistory.objects.only("results").get(pk=int(record_id))
                index = int(index_str)
                path = record.results[index].get("path", "")
            except (ImageHistory.DoesNotExist, ValueError, IndexError, AttributeError):
                raise Http404("记录不存在")
            return self._serve_file(path)

        raise Http404("未知媒体类型")


# ─── 视频生成历史 ─────────────────────────────────────────────────────────────

class VideoHistoryViewSet(viewsets.ModelViewSet):
    """
    视频生成历史 CRUD。

    GET    /api/video-history/          列表（最近 30 天，降序）
    POST   /api/video-history/          新建一条记录（含自动下载视频到本地）
    DELETE /api/video-history/{id}/     删除单条
    DELETE /api/video-history/clear/    清空所有
    """

    serializer_class     = VideoHistorySerializer
    authentication_classes = []
    permission_classes   = []
    http_method_names    = ["get", "post", "delete", "head", "options"]

    RETENTION_DAYS = 30

    def get_queryset(self):
        """仅返回最近 30 天的记录"""
        cutoff = timezone.now() - timedelta(days=self.RETENTION_DAYS)
        return VideoHistory.objects.filter(created_at__gte=cutoff)

    def perform_create(self, serializer):
        """
        保存时若 video_url 为远程链接，则自动下载到本地并写入 video_path。
        导出目录从数据库 Settings.export_path 读取，留空则用默认目录。
        下载在后台线程执行，不阻塞响应。
        """
        instance = serializer.save()
        video_url = instance.video_url
        task_id = instance.task_id

        if _is_remote_url(video_url) and not instance.video_path:
            import threading
            save_dir = Settings.get("export_path") or None
            def _do_download():
                local_path = _download_video(video_url, task_id or str(instance.id), base_dir=save_dir)
                if local_path:
                    VideoHistory.objects.filter(pk=instance.pk).update(video_path=local_path)
            threading.Thread(target=_do_download, daemon=True).start()

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, _request):
        """清空所有历史记录（不受 30 天限制）"""
        VideoHistory.objects.all().delete()
        return Response(status=204)


# ─── 图片生成历史 ─────────────────────────────────────────────────────────────

class ImageHistoryViewSet(viewsets.ModelViewSet):
    """
    图片生成历史 CRUD。

    GET    /api/image-history/          列表（最近 30 天，降序）
    POST   /api/image-history/          新建一条记录（含自动下载远程图片到本地）
    DELETE /api/image-history/{id}/     删除单条
    DELETE /api/image-history/clear/    清空所有
    """

    serializer_class       = ImageHistorySerializer
    authentication_classes = []
    permission_classes     = []
    http_method_names      = ["get", "post", "delete", "head", "options"]

    RETENTION_DAYS = 30

    def get_queryset(self):
        """仅返回最近 30 天的记录"""
        cutoff = timezone.now() - timedelta(days=self.RETENTION_DAYS)
        return ImageHistory.objects.filter(created_at__gte=cutoff)

    def perform_create(self, serializer):
        """
        保存时将 results 内每条有 image_data（base64 data URI）的图片写入磁盘，
        并将本地路径写回 results[].path。
        导出目录从数据库 Settings.export_path 读取，留空则用默认目录。
        写盘在后台线程执行，不阻塞响应。
        """
        instance = serializer.save()
        results = instance.results or []
        subdir = datetime.now().strftime("%m-%d")

        # 只处理有 image_data 且尚未写盘的条目
        has_work = any(
            isinstance(r, dict) and r.get("image_data") and not r.get("path")
            for r in results
        )
        if not has_work:
            return

        import threading
        save_dir = Settings.get("export_path") or None

        def _do_save():
            images_root = os.path.join(save_dir, "images") if save_dir else _DEFAULT_IMAGES_DIR
            folder = os.path.join(images_root, subdir)
            os.makedirs(folder, exist_ok=True)

            updated = False
            new_results = []
            for r in results:
                if not isinstance(r, dict) or not r.get("image_data") or r.get("path"):
                    new_results.append(r)
                    continue
                try:
                    data_uri = r["image_data"]
                    # data URI 格式：data:<mime>;base64,<data>
                    header, b64_data = data_uri.split(",", 1)
                    mime = header.split(":")[1].split(";")[0]   # image/jpeg / image/png …
                    ext_map = {
                        "image/jpeg": ".jpg", "image/jpg": ".jpg",
                        "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
                    }
                    ext = ext_map.get(mime, ".jpg")
                    filename = f"{datetime.now().strftime('%H%M%S%f')}_{r.get('index', 0)}{ext}"
                    local_path = os.path.join(folder, filename)
                    with open(local_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    r = {**r, "path": local_path}
                    updated = True
                    logger.info("✓ 图片已写盘: %s", local_path)
                except Exception as e:
                    logger.warning("✗ 图片写盘失败 index=%s: %s", r.get("index"), e)
                new_results.append(r)

            if updated:
                ImageHistory.objects.filter(pk=instance.pk).update(results=new_results)

        threading.Thread(target=_do_save, daemon=True).start()

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, _request):
        """清空所有历史记录（不受 30 天限制）"""
        ImageHistory.objects.all().delete()
        return Response(status=204)
