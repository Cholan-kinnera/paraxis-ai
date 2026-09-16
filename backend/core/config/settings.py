"""
Django settings for Paraxis AI Core Platform.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent

# Load environment variables from repo root .env if present
env_path = REPO_ROOT / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        pass

# Security settings
SECRET_KEY = os.getenv("APP_SECRET_KEY", "paraxis-core-dev-insecure-secret-key-replace-in-prod-1234")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local core
    "core",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.correlation.CorrelationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.tenancy.TenancyMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database Configuration (PostgreSQL 16 + pgvector)
POSTGRES_DB = os.getenv("POSTGRES_DB", "paraxis_dev")
POSTGRES_USER = os.getenv("POSTGRES_USER", "paraxis_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "paraxis_local_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    from urllib.parse import urlparse, parse_qs, unquote
    parsed_url = urlparse(DATABASE_URL)
    if parsed_url.path and parsed_url.path != "/":
        POSTGRES_DB = parsed_url.path.lstrip("/")
    if parsed_url.username:
        POSTGRES_USER = unquote(parsed_url.username)
    if parsed_url.password:
        POSTGRES_PASSWORD = unquote(parsed_url.password)
    if parsed_url.hostname:
        POSTGRES_HOST = parsed_url.hostname
    if parsed_url.port:
        POSTGRES_PORT = str(parsed_url.port)
    query_params = parse_qs(parsed_url.query)
    if "sslmode" in query_params and query_params["sslmode"]:
        POSTGRES_SSLMODE = query_params["sslmode"][0]

db_options = {}
if POSTGRES_SSLMODE:
    db_options["sslmode"] = POSTGRES_SSLMODE

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        "CONN_MAX_AGE": 60,
        "OPTIONS": db_options,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "core.User"
SILENCED_SYSTEM_CHECKS = ["auth.E003"]

# Django REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.jwt.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "core.permissions.rbac.IsAuthenticatedUser",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
# Correlation headers required by AGENTS.md §6 must survive browser preflight.
from corsheaders.defaults import default_headers  # noqa: E402
CORS_ALLOW_HEADERS = [*default_headers, "x-request-id", "x-trace-id", "x-tenant-id", "x-agent-run-id", "x-tool-call-id"]
CORS_EXPOSE_HEADERS = ["X-Request-ID", "X-Trace-ID"]
