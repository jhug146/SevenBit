from pathlib import Path

# Project root is three levels up: ui/website/settings.py -> ui/website/ -> ui/ -> root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "sevenbit-local-dev-only"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "ui.website.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "ui" / "website" / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "ui" / "website" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
