from django.db import models


class Item(models.Model):
    """示例数据模型（可根据业务需求修改）"""

    name = models.CharField(max_length=200, verbose_name="名称")
    description = models.TextField(blank=True, verbose_name="描述")
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "启用"),
            ("inactive", "停用"),
        ],
        default="active",
        verbose_name="状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "条目"
        verbose_name_plural = "条目列表"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
