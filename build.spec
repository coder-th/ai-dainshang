# -*- mode: python ; coding: utf-8 -*-
import os
import sys

project_root = os.path.dirname(os.path.abspath(SPEC))

sys.path.insert(0, os.path.join(project_root, "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("APP_BUNDLE_DIR", project_root)
os.environ.setdefault("APP_DATA_DIR", project_root)

import django
django.setup()

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ─── Data files ──────────────────────────────────────────────────────────────

datas = []
datas += collect_data_files("django")
datas += collect_data_files("rest_framework")
datas += collect_data_files("whitenoise")

frontend_dist = os.path.join(project_root, "frontend", "dist")
if os.path.exists(frontend_dist):
    datas.append((frontend_dist, os.path.join("frontend", "dist")))
else:
    print("[WARN] frontend/dist not found. Run: cd frontend && npm run build")

datas.append((os.path.join(project_root, "backend"), "backend"))

# ─── Hidden imports ───────────────────────────────────────────────────────────
# Use collect_submodules to avoid missing any submodule

hiddenimports = []

# Collect ALL submodules of third-party packages
hiddenimports += collect_submodules("django")
hiddenimports += collect_submodules("rest_framework")
hiddenimports += collect_submodules("whitenoise")
hiddenimports += collect_submodules("corsheaders")

# SQLite backend (required on Windows)
hiddenimports += [
    "django.db.backends.sqlite3",
    "_sqlite3",
]

# Our app modules
hiddenimports += [
    "apps",
    "apps.core",
    "apps.core.apps",
    "apps.core.models",
    "apps.core.serializers",
    "apps.core.views",
    "apps.core.urls",
    "apps.core.admin",
    "config",
    "config.settings",
    "config.urls",
    "config.wsgi",
]

# ─── Build ────────────────────────────────────────────────────────────────────

a = Analysis(
    [os.path.join(project_root, "main.py")],
    pathex=[project_root, os.path.join(project_root, "backend")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "PIL"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
