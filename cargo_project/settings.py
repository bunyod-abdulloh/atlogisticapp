"""
Django settings for cargo_project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Xavfsizlik — bularning barchasi .env faylidan o'qiladi, kodga yozilmaydi.
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-CHANGE-ME-IN-PRODUCTION")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", ).split(",") if h.strip()]

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "jazzmin",  # admin panel temasi — django.contrib.admin'dan OLDIN turishi shart
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "tracking",
    "shipments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CommonMiddleware'dan OLDIN turishi kerak
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cargo_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ['templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cargo_project.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASS"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS — frontend (HTML/CSS/JS) Django'dan alohida domen/portda ishga
# tushsa (masalan Live Server: http://127.0.0.1:5500) shu ro'yxatga qo'shing.
# Agar frontend Django'ning o'zidan (bir xil domen) berilsa, bu umuman kerak emas.
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",")
    if o.strip()
]

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "cargo_track": "20/min",
        "cargo_history": "30/min",
    },
}

# ---------------------------------------------------------------------------
# Jazzmin — Django admin uchun tayyor, chiroyli tema
# https://django-jazzmin.readthedocs.io/
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    # "hide_apps": ["auth"],
    "site_title": "A&T Logistics",
    "site_header": "A&T Logistics",
    "site_brand": "A&T Logistics",

    "welcome_sign": "A&T Logistics boshqaruv paneli",
    "copyright": "A&T Logistics",

    "show_sidebar": True,
    "navigation_expanded": True,

    "order_with_respect_to": [
        "tracking",
        "auth",
    ],

    "icons": {
        "tracking.Cargo": "fas fa-boxes-stacked",
        "tracking.CargoStatusUpdate": "fas fa-route",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
    },

    "custom_css": "admin/css/admin-custom.css",
    "custom_js": "js/admin-custom.js",

    "site_logo": "img/logo.png",
    "site_icon": "img/logo.png",

    "custom_links": {
        "shipments": [{
            "name": "Statistika",
            "url": "admin:shipments_dashboard",
            "icon": "fas fa-chart-line",
            "permissions": ["shipments.view_shipment"],
        }],
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "slate",
    "dark_mode_theme": "slate",  # dark rejimda ham qaysi tema ishlatilishini aniq ko'rsatamiz
    "default_theme_mode": "dark",

    "navbar_small_text": False,
    "sidebar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    "brand_colour": "navbar-warning",
    "accent": "accent-warning",
    "navbar": "navbar-warning",

    "no_navbar_border": False,

    "sidebar": "sidebar-light-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
}
