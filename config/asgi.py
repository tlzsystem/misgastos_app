"""
ASGI config for MisGastos project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""
import os
from pathlib import Path
from django.core.asgi import get_asgi_application

try:
    import environ

    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / ".env"
    if env_file.exists():
        environ.Env.read_env(str(env_file))
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
