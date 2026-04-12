from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="VideoHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "model",
                    models.CharField(max_length=100, verbose_name="模型ID"),
                ),
                (
                    "model_name",
                    models.CharField(max_length=200, verbose_name="模型名称"),
                ),
                (
                    "prompt",
                    models.TextField(verbose_name="提示词"),
                ),
                (
                    "thumbnails",
                    models.JSONField(default=list, verbose_name="参考图缩略图"),
                ),
                (
                    "image_count",
                    models.IntegerField(default=0, verbose_name="参考图数量"),
                ),
                (
                    "ratio",
                    models.CharField(blank=True, max_length=10, verbose_name="视频比例"),
                ),
                (
                    "duration",
                    models.IntegerField(default=8, verbose_name="视频时长(秒)"),
                ),
                (
                    "task_id",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="任务ID"
                    ),
                ),
                (
                    "status",
                    models.CharField(max_length=20, verbose_name="状态"),  # done | error
                ),
                (
                    "video_url",
                    models.TextField(blank=True, null=True, verbose_name="视频URL"),
                ),
                (
                    "error",
                    models.TextField(blank=True, null=True, verbose_name="错误信息"),
                ),
                (
                    "generation_time_ms",
                    models.IntegerField(default=0, verbose_name="生成耗时(ms)"),
                ),
                (
                    "enhanced_prompt",
                    models.TextField(blank=True, verbose_name="AI优化提示词"),
                ),
                (
                    "video_file_size",
                    models.CharField(blank=True, max_length=50, verbose_name="文件大小"),
                ),
            ],
            options={
                "verbose_name": "视频生成历史",
                "verbose_name_plural": "视频生成历史列表",
                "ordering": ["-created_at"],
            },
        ),
    ]
