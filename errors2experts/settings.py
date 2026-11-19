"""
Django settings for errors2experts project.
"""
import os
from dotenv import load_dotenv
from pathlib import Path
import cloudinary
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "local-development-secret-key")



DEBUG = True


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "errors2experts.com",
    "www.errors2experts.com",
    "errors2experts.up.railway.app",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "cloudinary",
    "main",
    "workshops",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'errors2experts.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.latest_offer",
            ],
        },
    },
]

WSGI_APPLICATION = 'errors2experts.wsgi.application'


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# media
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

ADMIN_NOTIFICATION_EMAIL = os.getenv(
    "ADMIN_NOTIFICATION_EMAIL",
    "errors2experts.official@gmail.com",
)

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")



CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
}



STORAGES = {
    "default": {
        # "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
         "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage",
    },
}

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://errors2experts.up.railway.app",
    ).split(",")
    if origin.strip()
]

# Railway forwards the original HTTPS protocol through this header.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Keep HSTS disabled until the new production deployment is verified.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


UPI_ID = os.getenv(
    "UPI_ID",
    "",
)

UPI_PAYEE_NAME = os.getenv(
    "UPI_PAYEE_NAME",
    "Errors2Experts",
)


# Workshop application settings (mounted at /workshop/)
DATA_DIR = BASE_DIR / "data"
REGISTRATIONS_XLSX = DATA_DIR / "registrations.xlsx"
PAYMENTS_DIR = DATA_DIR / "payments"
MAX_SCREENSHOT_BYTES = 4 * 1024 * 1024
CERT_TEMPLATES_DIR = DATA_DIR / "certificate_templates"
CERT_FONT_DIR = BASE_DIR / "main" / "static" / "workshop" / "fonts"
MAX_CERT_TEMPLATE_BYTES = 15 * 1024 * 1024
ANNOUNCE_FILES_DIR = DATA_DIR / "announce_files"
MAX_ANNOUNCE_FILE_BYTES = 5 * 1024 * 1024
MAX_ANNOUNCE_TOTAL_BYTES = 12 * 1024 * 1024
MAX_ANNOUNCE_FILES = 6
ANNOUNCE_BATCH = 40
SITE_URL = os.getenv("SITE_URL", "https://errors2experts.com").rstrip("/")
POST_SUBMIT_REDIRECT_URL = os.getenv("POST_SUBMIT_REDIRECT_URL", "https://errors2experts.com/")
ORG = {
    "name": os.getenv("ORG_NAME", "Errors2Experts IT Training & IT Services"),
    "short": os.getenv("ORG_SHORT_NAME", "Errors2Experts"),
    "website": os.getenv("ORG_WEBSITE", "https://errors2experts.com/"),
    "email": os.getenv("ORG_EMAIL", "errors2experts.official@gmail.com"),
    "phone": os.getenv("ORG_PHONE", "9363342646"),
    "phones": [p.strip() for p in os.getenv("ORG_PHONES", "9363342646,9043341503,8015306807").split(",") if p.strip()],
    "address": os.getenv("ORG_ADDRESS", "Dindigul, Tamil Nadu"),
    "registration": os.getenv("ORG_REGISTRATION", "MSME Registered (UDYAM-TN-06-0108008)"),
    "social": {k: os.getenv("SOCIAL_" + k.upper()) for k in ("instagram", "linkedin", "youtube", "facebook", "whatsapp") if os.getenv("SOCIAL_" + k.upper())},
}
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587") or 587)
EMAIL_USE_TLS = EMAIL_PORT != 465
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = f'{os.getenv("MAIL_FROM_NAME", "Swetha")} <{EMAIL_HOST_USER or "noreply@example.com"}>'
ADMIN_NOTIFY_EMAIL = os.getenv("ADMIN_NOTIFY_EMAIL", "")
FILE_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
