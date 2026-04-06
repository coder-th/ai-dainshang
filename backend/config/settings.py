"""
Django 配置文件
支持开发环境和 PyInstaller 打包两种运行模式
"""
import os
import sys

# ─── 路径解析 ────────────────────────────────────────────────────────────────

# APP_BUNDLE_DIR：只读资源根目录（打包后为 _MEIPASS，开发时为项目根）
BUNDLE_DIR = os.environ.get(
    "APP_BUNDLE_DIR",
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

# APP_DATA_DIR：可写数据目录（打包后为 exe 所在目录，开发时为项目根）
DATA_DIR = os.environ.get("APP_DATA_DIR", BUNDLE_DIR)

# ─── 基础设置 ────────────────────────────────────────────────────────────────

SECRET_KEY = "django-insecure-change-this-in-production-abc123xyz"

# 打包后关闭 DEBUG
DEBUG = not getattr(sys, "frozen", False)

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

# ─── 应用列表 ────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.core",
]

# 开发模式下让 WhiteNoise 接管 runserver 的静态文件服务
if not getattr(sys, "frozen", False):
    INSTALLED_APPS.insert(5, "whitenoise.runserver_nostatic")

# ─── 中间件 ──────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ─── 模板配置 ────────────────────────────────────────────────────────────────

# Vue 构建产物的 index.html 所在目录
FRONTEND_DIST_DIR = os.path.join(BUNDLE_DIR, "frontend", "dist")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─── 数据库 ──────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DATA_DIR, "db.sqlite3"),
    }
}

# ─── 密码验证 ────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── 国际化 ──────────────────────────────────────────────────────────────────

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ─── 静态文件 ────────────────────────────────────────────────────────────────

STATIC_URL = "/static/"

# WhiteNoise 从 Vue 构建产物目录直接服务根路径文件（如 /assets/、/favicon.ico）
WHITENOISE_ROOT = FRONTEND_DIST_DIR

# collectstatic 收集目录（用于 PyInstaller 打包前执行）
STATIC_ROOT = os.path.join(BUNDLE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─── CORS ────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:9527",
    "http://localhost:9527",
    "http://localhost:5173",  # Vite 开发服务器
]

# ─── DRF ─────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}

# ─── 日志配置 ────────────────────────────────────────────────────────────────

LOGS_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "outbound_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "outbound.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # 对外 HTTP 请求日志（views.py 中使用 outbound 这个 logger）
        "outbound": {
            "handlers": ["console", "outbound_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ─── 其他 ─────────────────────────────────────────────────────────────────────

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
