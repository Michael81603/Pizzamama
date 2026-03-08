import os

from .base import *  # noqa: F401,F403


DEBUG = env_bool("DJANGO_DEBUG", True)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
