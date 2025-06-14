from pathlib import Path
import os
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-4hs#$%^&*()_+=-0987654321"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "django_celery_results",
    "frameworks_and_drivers.django.parsing.data_manager",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "frameworks_and_drivers.django.parsing.parsing.urls"

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

# WSGI_APPLICATION = 'parsing.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "ATOMIC_REQUESTS": False,
        "DISABLE_SERVER_SIDE_CURSORS": True,  # required when using pgbouncer's pool_mode=transaction
    },
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "HOST": "130.193.41.98",
#         "PORT": "5532",
#         "NAME": "afisha",
#         "USER": "afisha",
#         "PASSWORD": "password",
#         "ATOMIC_REQUESTS": False,
#         "DISABLE_SERVER_SIDE_CURSORS": True,  # required when using pgbouncer's pool_mode=transaction
#     },
# }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Moscow"  # Устанавливаем московское время

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

CELERY_TIMEZONE = "Europe/Moscow"  # Используем московское время для Celery
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Настройки для django-celery-beat
DJANGO_CELERY_BEAT_TZ_AWARE = True

# Расписание задач Celery Beat
CELERY_BEAT_SCHEDULE = {
    "run-main-parsers-morning": {
        "task": "run_main_parsers",
        "schedule": crontab(hour=9, minute=0),  # Запуск в 9:00
        "options": {
            "expires": 3600,  # Задача истекает через час
        },
    },
    "run-main-parsers-evening": {
        "task": "run_main_parsers",
        "schedule": crontab(hour=18, minute=0),  # Запуск в 18:00
        "options": {
            "expires": 3600,  # Задача истекает через час
        },
    },
}

MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")

AWS_ACCESS_KEY_ID = MINIO_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = MINIO_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = MINIO_BUCKET_NAME
AWS_S3_ENDPOINT_URL = MINIO_ENDPOINT

# MinIO/S3 настройки для решения проблемы с 404
AWS_DEFAULT_ACL = "public-read"  # Делаем файлы публично доступными
AWS_QUERYSTRING_AUTH = False  # Отключаем подписанные URL
AWS_S3_FILE_OVERWRITE = False  # Не перезаписывать файлы с одинаковыми именами
AWS_S3_SECURE_URLS = True  # Использовать HTTPS
AWS_S3_CUSTOM_DOMAIN = "afishabot.ru"  # Ваш кастомный домен

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console"],
            "level": "INFO",
        },
        "frameworks_and_drivers": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "interface_adapters": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {  # Логирование SQL запросов
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
