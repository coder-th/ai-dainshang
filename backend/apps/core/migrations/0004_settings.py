from django.db import migrations, models


class Migration(migrations.Migration):
    """
    新增 Settings 表：key-value 形式存储全局配置。
    初始用途：持久化用户配置的导出路径（export_path）。
    """

    dependencies = [
        ("core", "0003_videohistory_video_path_imagehistory_local_path"),
    ]

    operations = [
        migrations.CreateModel(
            name="Settings",
            fields=[
                (
                    "key",
                    models.CharField(
                        max_length=100,
                        primary_key=True,
                        serialize=False,
                        verbose_name="配置键",
                    ),
                ),
                (
                    "value",
                    models.TextField(blank=True, verbose_name="配置值"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
            ],
            options={
                "verbose_name": "系统配置",
                "verbose_name_plural": "系统配置",
            },
        ),
    ]
