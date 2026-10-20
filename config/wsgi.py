"""
WSGI config for MisGastos project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

try:
    import environ

    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / ".env"
    if env_file.exists():
        environ.Env.read_env(str(env_file), overwrite=True)
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
if os.environ.get("DJANGO_SETTINGS_MODULE", "").startswith("app."):
    os.environ["DJANGO_SETTINGS_MODULE"] = os.environ["DJANGO_SETTINGS_MODULE"].replace(
        "app.", "config.", 1
    )

application = get_wsgi_application()
