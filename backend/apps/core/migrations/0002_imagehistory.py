from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImageHistory",
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
                    "provider",
                    models.CharField(blank=True, max_length=50, verbose_name="供应商"),
                ),
                (
                    "prompt",
                    models.TextField(verbose_name="提示词"),
                ),
                (
                    "aspect_ratio",
                    models.CharField(blank=True, max_length=20, verbose_name="图片比例"),
                ),
                (
                    "image_size",
                    models.CharField(blank=True, max_length=20, verbose_name="图片分辨率"),
                ),
                (
                    "search",
                    models.BooleanField(default=False, verbose_name="是否联网搜索"),
                ),
                (
                    "base_image_thumbs",
                    models.JSONField(default=list, verbose_name="底图缩略图"),
                ),
                (
                    "ref_image_thumbs",
                    models.JSONField(default=list, verbose_name="参考图缩略图"),
                ),
                (
                    "results",
                    models.JSONField(
                        default=list,
                        verbose_name="生成结果列表",
                        # [{index, image_data (base64 data URI), error, file_size, done_at}]
                    ),
                ),
                (
                    "status",
                    models.CharField(max_length=20, verbose_name="状态"),  # done | error | partial
                ),
                (
                    "generation_time_ms",
                    models.IntegerField(default=0, verbose_name="生成耗时(ms)"),
                ),
            ],
            options={
                "verbose_name": "图片生成历史",
                "verbose_name_plural": "图片生成历史列表",
                "ordering": ["-created_at"],
            },
        ),
    ]
