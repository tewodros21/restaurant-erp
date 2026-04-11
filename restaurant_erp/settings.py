from decouple import config
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Core ─────────────────────────────────────────────────
SECRET_KEY    = config('SECRET_KEY')
DEBUG         = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Safety — never force HTTPS in dev
SECURE_SSL_REDIRECT = False   # ← add this line here

# ─── Apps ─────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    'django_celery_beat',
    'accounts',
    'pos',
    'tables',
    'menu',
    'inventory',
    'hr',
    'assets',
    'finance',
    'notifications',
]

# ─── Middleware ────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'restaurant_erp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'restaurant_erp.wsgi.application'

# ─── Database ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
    }
}

# ─── Auth ─────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─── JWT ──────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

# ─── CORS ─────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ─── Static & Media ───────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Security (Production Only) ───────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    X_FRAME_OPTIONS                = 'DENY'
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT            = False
    SESSION_COOKIE_SECURE          = False
    CSRF_COOKIE_SECURE             = False

# ─── Celery ───────────────────────────────────────────────
CELERY_BROKER_URL        = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND    = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Africa/Addis_Ababa'

CELERY_BEAT_SCHEDULE = {
    'check-low-stock-daily': {
        'task':     'notifications.tasks.check_low_stock_all_branches',
        'schedule': crontab(hour=8, minute=0),
    },
    'reservation-reminders': {
        'task':     'notifications.tasks.send_reservation_reminders',
        'schedule': crontab(minute='*/15'),
    },
    'check-maintenance-daily': {
        'task':     'notifications.tasks.check_maintenance_due',
        'schedule': crontab(hour=9, minute=0),
    },
    'monthly-depreciation': {
        'task':     'notifications.tasks.apply_monthly_depreciation_all',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
    'daily-backup': {
        'task':     'core.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0),
    },
}

# ─── Logging ──────────────────────────────────────────────
import os
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style':  '{'
        },
    },
    'handlers': {
        'file': {
            'level':     'ERROR',
            'class':     'logging.FileHandler',
            'filename':  BASE_DIR / 'logs/errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers':  ['file', 'console'],
            'level':     'ERROR',
            'propagate': True,
        },
    },
}

# ─── Default Auto Field ───────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'