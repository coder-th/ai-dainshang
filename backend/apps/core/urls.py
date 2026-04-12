from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    GenerateView, VideoGenerateView, VideoTaskQueryView,
    ItemViewSet, ProxyImageView, MediaFileView, SettingsView,
    VideoHistoryViewSet, ImageHistoryViewSet,
)

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")
router.register(r"video-history", VideoHistoryViewSet, basename="video-history")
router.register(r"image-history", ImageHistoryViewSet, basename="image-history")

urlpatterns = [
    path("", include(router.urls)),
    path("generate/", GenerateView.as_view(), name="generate"),
    path("generate-video/", VideoGenerateView.as_view(), name="generate-video"),
    path("video-task/", VideoTaskQueryView.as_view(), name="video-task"),
    path("proxy-image/", ProxyImageView.as_view(), name="proxy-image"),
    # 系统配置（GET/PUT/DELETE）
    path("settings/<str:key>/", SettingsView.as_view(), name="settings"),
    # 本地媒体文件服务：通过记录 ID 读取数据库中存储的绝对路径
    path("media/video/", MediaFileView.as_view(), {"media_type": "video"}, name="media-video"),
    path("media/image/", MediaFileView.as_view(), {"media_type": "image"}, name="media-image"),
]
