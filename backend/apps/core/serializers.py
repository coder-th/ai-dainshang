from rest_framework import serializers
from .models import Item, VideoHistory, ImageHistory, Settings


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ["key", "value", "updated_at"]
        read_only_fields = ["updated_at"]


class VideoHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoHistory
        fields = [
            "id",
            "created_at",
            "model",
            "model_name",
            "prompt",
            "thumbnails",
            "image_count",
            "ratio",
            "duration",
            "task_id",
            "status",
            "video_url",
            "video_path",
            "error",
            "generation_time_ms",
            "enhanced_prompt",
            "video_file_size",
        ]
        read_only_fields = ["id", "created_at"]


class ImageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageHistory
        fields = [
            "id",
            "created_at",
            "model",
            "model_name",
            "provider",
            "prompt",
            "aspect_ratio",
            "image_size",
            "search",
            "base_image_thumbs",
            "ref_image_thumbs",
            "results",
            "status",
            "generation_time_ms",
        ]
        read_only_fields = ["id", "created_at"]
