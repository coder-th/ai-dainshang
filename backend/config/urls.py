"""
URL 路由配置
- /api/     → REST API
- /admin/   → Django 管理后台
- 其余路径   → 返回 Vue SPA 的 index.html
"""
import os
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, include, re_path


def spa_view(request, path=""):
    """返回 Vue SPA 的 index.html，支持前端路由"""
    index_file = os.path.join(settings.FRONTEND_DIST_DIR, "index.html")
    if not os.path.exists(index_file):
        raise Http404("前端资源未找到，请先执行 npm run build")
    return FileResponse(open(index_file, "rb"), content_type="text/html; charset=utf-8")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    # 捕获所有其他路径，交给 Vue Router 处理
    re_path(r"^(?!api/|admin/|static/).*$", spa_view),
]
