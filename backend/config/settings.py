from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers

from .env import env_bool, env_list, load_root_env
from .storage import storage_settings

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
    "apps.assistant",
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
    "apps.outreach",
    "apps.subscriptions",
    "apps.integrations",
    "apps.marketing",
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
# Business dates follow the Zambia beta market; aware timestamps remain UTC in storage.
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = __import__("os").getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = storage_settings()
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_BACKEND = __import__("os").getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = __import__("os").getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(__import__("os").getenv("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = __import__("os").getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = __import__("os").getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(__import__("os").getenv("EMAIL_TIMEOUT", "20"))
DEFAULT_FROM_EMAIL = __import__("os").getenv("EMAIL_FROM_ADDRESS", "no-reply@dwella.local")
FRONTEND_URL = __import__("os").getenv("FRONTEND_URL", "http://localhost:5173")
HANDY_AGENT_SIGNING_SECRET = __import__("os").getenv("HANDY_AGENT_SIGNING_SECRET", "")
HANDY_AGENT_URL = __import__("os").getenv("VITE_HANDY_AGENT_URL", "")
HANDY_AGENT_ISSUER = __import__("os").getenv(
    "HANDY_AGENT_ISSUER", "https://api.dwella.properties"
)
HANDY_AGENT_AUDIENCE = __import__("os").getenv("HANDY_AGENT_AUDIENCE", "handy-agent")
HANDY_AGENT_TOKEN_TTL_SECONDS = int(
    __import__("os").getenv("HANDY_AGENT_TOKEN_TTL_SECONDS", "900")
)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("APP_SECURE_SSL_REDIRECT", False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = env_bool("APP_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("APP_COOKIE_SECURE", False)
CONTENT_SECURITY_POLICY = __import__("os").getenv(
    "CONTENT_SECURITY_POLICY",
    "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
)

CORS_ALLOW_HEADERS = [
    *default_headers,
    "x-dwella-workspace",
    "x-request-id",
    "x-dwella-signing-session",
]

CORS_ALLOWED_ORIGINS = env_list(
    "APP_CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.common.authentication.WorkspaceSessionAuthentication",
        "apps.common.authentication.WorkspaceTokenAuthentication",
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
    # Without a proxy count DRF keys throttles on the whole X-Forwarded-For
    # header, which a client can prefix with any value to get a fresh limit.
    # With it set, only the address our own proxy appended is trusted.
    "NUM_PROXIES": int(__import__("os").getenv("APP_TRUSTED_PROXY_COUNT") or 0) or None,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": __import__("os").getenv("THROTTLE_ANON_RATE", "100/hour"),
        "user": __import__("os").getenv("THROTTLE_USER_RATE", "1000/hour"),
        "support_session": "10/hour",
        "platform_write": "20/minute",
        "login": __import__("os").getenv("THROTTLE_LOGIN_RATE", "8/minute"),
        "registration": __import__("os").getenv("THROTTLE_REGISTRATION_RATE", "5/hour"),
        "password_reset": __import__("os").getenv("THROTTLE_PASSWORD_RESET_RATE", "3/hour"),
        "two_factor": __import__("os").getenv("THROTTLE_2FA_RATE", "10/minute"),
        "handy_agent_token": __import__("os").getenv(
            "THROTTLE_HANDY_AGENT_TOKEN_RATE", "20/hour"
        ),
        "handy_agent_action": __import__("os").getenv(
            "THROTTLE_HANDY_AGENT_ACTION_RATE", "120/hour"
        ),
        "beta_application": __import__("os").getenv("THROTTLE_BETA_APPLICATION_RATE", "5/hour"),
    },
}

BETA_REGISTRATION_OPEN = (
    __import__("os").getenv("APP_BETA_REGISTRATION_OPEN", "false").lower() == "true"
)
# Beta applicant emails stay off until real delivery is configured, so nothing is
# marked as sent while EMAIL_BACKEND is still the console. Turning it on later
# catches up any welcome emails that were missed.
BETA_EMAILS_ENABLED = env_bool("APP_BETA_EMAILS_ENABLED", False)
BETA_OPEN_DATE = __import__("os").getenv("APP_BETA_OPEN_DATE", "2026-11-18")
BETA_EMAIL_REPLY_TO = __import__("os").getenv("APP_BETA_EMAIL_REPLY_TO", "")
MARKETING_SITE_URL = __import__("os").getenv("MARKETING_SITE_URL", "https://dwella.properties")
PUBLIC_API_URL = __import__("os").getenv("PUBLIC_API_URL", "http://localhost:8000")
OPENAPI_SERVER_URL = __import__("os").getenv(
    "OPENAPI_SERVER_URL", PUBLIC_API_URL.removesuffix("/api")
)

SPECTACULAR_SETTINGS = {
    "TITLE": "Dwella Suite API",
    "DESCRIPTION": "Property management APIs for Dwella Suite.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [{"url": OPENAPI_SERVER_URL}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "HandyAgentBearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

CELERY_BROKER_URL = __import__("os").getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Throttles and rendered document pages must be shared by every gunicorn worker.
# Without an explicit cache URL each process keeps its own in-memory copy.
if __import__("os").getenv("APP_CACHE_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": __import__("os").getenv("APP_CACHE_URL"),
        }
    }

# ZRA Smart Invoice. Dwella has no VSDC yet, so a fake one answers in its
# place; point this at a real client class once ZRA issues the device.
ZRA_VSDC_CLIENT = __import__("os").getenv(
    "ZRA_VSDC_CLIENT", "apps.integrations.zra.client.FakeVsdcClient"
)
