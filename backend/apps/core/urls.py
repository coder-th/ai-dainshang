from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GenerateView, VideoGenerateView, ItemViewSet, ProxyImageView

router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")

urlpatterns = [
    path("", include(router.urls)),
    path("generate/", GenerateView.as_view(), name="generate"),
    path("generate-video/", VideoGenerateView.as_view(), name="generate-video"),
    path("proxy-image/", ProxyImageView.as_view(), name="proxy-image"),
]
