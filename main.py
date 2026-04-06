"""
Backend entry point - starts Django server only.
Browser/window is managed by Electron, not this process.
"""
import sys
import os


def fix_stdio():
    """Redirect stdout/stderr to log file when running as windowed exe (no console)."""
    if getattr(sys, "frozen", False) and sys.stdout is None:
        log_path = os.path.join(os.path.dirname(sys.executable), "app.log")
        log_file = open(log_path, "w", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file


def get_resource_path(relative_path=""):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path) if relative_path else base


def get_data_dir():
    # Electron passes APP_DATA_DIR = app.getPath('userData') via env
    return os.environ.get(
        "APP_DATA_DIR",
        os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__)),
    )


def setup_environment():
    backend_path = get_resource_path("backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["APP_BUNDLE_DIR"] = get_resource_path()
    os.environ["APP_DATA_DIR"] = get_data_dir()


def run_migrations():
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", "--run-syncdb", verbosity=0)


def start_server():
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:9527", "--noreload"])


def main():
    fix_stdio()
    setup_environment()
    run_migrations()
    start_server()


if __name__ == "__main__":
    main()
