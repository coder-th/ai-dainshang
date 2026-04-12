from django.db import migrations, models


class Migration(migrations.Migration):
    """
    VideoHistory 增加 video_path（本地视频路径）字段。
    ImageHistory 的 results 字段本身为 JSONField，每条结果内新增 path 子字段
    由应用层负责写入，无需 schema 变更。
    """

    dependencies = [
        ("core", "0002_imagehistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="videohistory",
            name="video_path",
            field=models.TextField(blank=True, null=True, verbose_name="本地视频路径"),
        ),
    ]
