from pathlib import Path

import dj_database_url

from .env import env_bool, env_list, load_root_env

load_root_env()

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

SECRET_KEY = __import__("os").getenv("APP_SECRET_KEY", "dev-only-change-me")
DEBUG = env_bool("APP_DEBUG", False)
ALLOWED_HOSTS = env_list("APP_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("APP_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    "rest_framework.authtoken",
    "apps.common",
    "apps.accounts",
    "apps.organizations",
    "apps.properties",
    "apps.owners",
    "apps.tenants",
    "apps.leases",
    "apps.billing",
    "apps.maintenance",
    "apps.inspections",
    "apps.documents",
    "apps.notifications",
    "apps.reports",
    "apps.audit",
    "apps.subscriptions",
    "apps.integrations",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
    "apps.audit.middleware.RequestAuditContextMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
        conn_max_age=60,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = __import__("os").getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_BACKEND = __import__("os").getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = __import__("os").getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(__import__("os").getenv("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = __import__("os").getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = __import__("os").getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = __import__("os").getenv("EMAIL_FROM_ADDRESS", "no-reply@dwella.local")
FRONTEND_URL = __import__("os").getenv("FRONTEND_URL", "http://localhost:5173")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("APP_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("APP_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("APP_COOKIE_SECURE", False)
CONTENT_SECURITY_POLICY = __import__("os").getenv(
    "CONTENT_SECURITY_POLICY",
    "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
)

CORS_ALLOWED_ORIGINS = env_list(
    "APP_CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "apps.common.responses.EnvelopedJSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.common.responses.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": __import__("os").getenv("THROTTLE_ANON_RATE", "100/hour"),
        "user": __import__("os").getenv("THROTTLE_USER_RATE", "1000/hour"),
        "login": __import__("os").getenv("THROTTLE_LOGIN_RATE", "8/minute"),
        "password_reset": __import__("os").getenv("THROTTLE_PASSWORD_RESET_RATE", "3/hour"),
        "two_factor": __import__("os").getenv("THROTTLE_2FA_RATE", "10/minute"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Dwella Suite API",
    "DESCRIPTION": "Property management APIs for Dwella Suite.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_BROKER_URL = __import__("os").getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
