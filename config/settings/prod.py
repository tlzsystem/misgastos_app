"""
Production settings for MisGastos project.
Enforces strict security, WhiteNoise compression, and production database settings.
"""
from .base import *  # noqa: F403, F401

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# Database configuration for production:
# Supports either DATABASE_URL (from base.py) or individual DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT env vars
if os.environ.get("DB_NAME") and not os.environ.get("DATABASE_URL"):  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),  # noqa: F405
            "NAME": os.environ.get("DB_NAME"),  # noqa: F405
            "USER": os.environ.get("DB_USER", ""),  # noqa: F405
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),  # noqa: F405
            "HOST": os.environ.get("DB_HOST", "localhost"),  # noqa: F405
            "PORT": os.environ.get("DB_PORT", "5432"),  # noqa: F405
        }
    }

# Database connection pooling
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa: F405

# Security settings for HTTPS / Production (configurable via .env)
USE_HTTPS = env.bool("USE_HTTPS", default=False)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=USE_HTTPS)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=USE_HTTPS)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=USE_HTTPS)  # noqa: F405
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS settings
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000 if USE_HTTPS else 0)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS

# Static files storage with compression and manifest hashing
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Logging configuration for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="ERROR"),  # noqa: F405
            "propagate": False,
        },
    },
}
