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


# ─── 全局系统配置 ─────────────────────────────────────────────────────────────

class Settings(models.Model):
    """
    key-value 形式的系统配置表。
    当前已知键：
      export_path  用户配置的文件导出根目录（视频/图片下载到此目录下）
    """

    key        = models.CharField(max_length=100, primary_key=True, verbose_name="配置键")
    value      = models.TextField(blank=True, verbose_name="配置值")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name        = "系统配置"
        verbose_name_plural = "系统配置"

    def __str__(self):
        return f"{self.key}={self.value[:40]}"

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """读取配置值，不存在时返回 default。"""
        try:
            return cls.objects.get(pk=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key: str, value: str) -> None:
        """写入配置值（upsert）。"""
        cls.objects.update_or_create(pk=key, defaults={"value": value})


# ─── 视频生成历史 ──────────────────────────────────────────────────────────────

class VideoHistory(models.Model):
    """
    视频生成历史记录。

    每次视频任务达到终态（done / error）时写入一条记录。
    接口层负责过滤 30 天以外的数据；本模型不设软删除，直接物理删除。
    """

    created_at         = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    model              = models.CharField(max_length=100, verbose_name="模型ID")
    model_name         = models.CharField(max_length=200, verbose_name="模型名称")
    prompt             = models.TextField(verbose_name="提示词")
    thumbnails         = models.JSONField(default=list, verbose_name="参考图缩略图")
    image_count        = models.IntegerField(default=0, verbose_name="参考图数量")
    ratio              = models.CharField(max_length=10, blank=True, verbose_name="视频比例")
    duration           = models.IntegerField(default=8, verbose_name="视频时长(秒)")
    task_id            = models.CharField(max_length=200, blank=True, null=True, verbose_name="任务ID")
    status             = models.CharField(max_length=20, verbose_name="状态")   # done | error
    video_url          = models.TextField(blank=True, null=True, verbose_name="视频URL")
    error              = models.TextField(blank=True, null=True, verbose_name="错误信息")
    generation_time_ms = models.IntegerField(default=0, verbose_name="生成耗时(ms)")
    enhanced_prompt    = models.TextField(blank=True, verbose_name="AI优化提示词")
    video_file_size    = models.CharField(max_length=50, blank=True, verbose_name="文件大小")
    video_path         = models.TextField(blank=True, null=True, verbose_name="本地视频路径")

    class Meta:
        verbose_name        = "视频生成历史"
        verbose_name_plural = "视频生成历史列表"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.model} @ {self.created_at:%Y-%m-%d %H:%M}"


# ─── 图片生成历史 ──────────────────────────────────────────────────────────────

class ImageHistory(models.Model):
    """
    图片生成历史记录。

    每次图片生成完成后写入一条记录，包含所有批次结果。
    images 字段存储 base64 data URI（http/https 图片由前端转换后上传）。
    接口层负责过滤 30 天以外的数据；本模型不设软删除，直接物理删除。
    """

    created_at        = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    model             = models.CharField(max_length=100, verbose_name="模型ID")
    model_name        = models.CharField(max_length=200, verbose_name="模型名称")
    provider          = models.CharField(max_length=50, blank=True, verbose_name="供应商")
    prompt            = models.TextField(verbose_name="提示词")
    aspect_ratio      = models.CharField(max_length=20, blank=True, verbose_name="图片比例")
    image_size        = models.CharField(max_length=20, blank=True, verbose_name="图片分辨率")
    search            = models.BooleanField(default=False, verbose_name="是否联网搜索")
    base_image_thumbs = models.JSONField(default=list, verbose_name="底图缩略图")
    ref_image_thumbs  = models.JSONField(default=list, verbose_name="参考图缩略图")
    results           = models.JSONField(default=list, verbose_name="生成结果列表")
    # results 内每条：{index, image_data (base64 data URI), path (本地路径), error, file_size, done_at}
    status            = models.CharField(max_length=20, verbose_name="状态")  # done | error | partial
    generation_time_ms = models.IntegerField(default=0, verbose_name="生成耗时(ms)")

    class Meta:
        verbose_name        = "图片生成历史"
        verbose_name_plural = "图片生成历史列表"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.model} @ {self.created_at:%Y-%m-%d %H:%M}"

