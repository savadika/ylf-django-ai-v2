"""Deterministic settings for local and CI test runs."""
import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-django-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-at-least-32-bytes")

from .settings import *  # noqa: E402,F403

TESTING = True
DEBUG = False
SWAGGER_ENABLED = False
SECRET_KEY = "test-only-django-secret"
JWT_SECRET_KEY = "test-only-jwt-secret-at-least-32-bytes"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unidjango-tests",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
