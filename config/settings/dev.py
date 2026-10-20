"""
Development settings for MisGastos project.
Intended for local development only.
"""
from .base import *  # noqa: F403, F401

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405

ALLOWED_HOSTS = env.list(  # noqa: F405
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "testserver"],
)

# Email backend for local development prints emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable caching of static files during development
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
