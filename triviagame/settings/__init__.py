"""
settings.py but with space to store .env files next door
"""

import os
from pathlib import Path

from decouple import config, Csv
from django.contrib.messages import constants as message_constants
from dj_database_url import parse as db_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='divine-mountain-3508.fly.dev, trivia.vtbassmatt.com',
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in config(
    'ALLOWED_HOSTS',
    default='divine-mountain-3508.fly.dev, trivia.vtbassmatt.com',
    cast=Csv(),
)]


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'guardian',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_htmx',
    'runserveronhostname',
    'game.apps.GameConfig',
    'host.apps.HostConfig',
    'django.forms',
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'triviagame.middleware.NonHtmlDebugToolbarMiddleware', # enable only in local dev
    'triviagame.middleware.MultipleProxyMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'triviagame.middleware.htmx_message_middleware',
]

ROOT_URLCONF = 'triviagame.urls'

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

WSGI_APPLICATION = 'triviagame.wsgi.application'
ASGI_APPLICATION = 'triviagame.asgi.application'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# Messages framework -> Bootstrap 5
MESSAGE_TAGS = {
    message_constants.INFO: 'primary',
    message_constants.DEBUG: 'info',
    message_constants.ERROR: 'danger',
}

# Database

DATABASES = {
    'default': config(
        'DATABASE_URL',
        default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"),
        cast=db_url,
    )
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_URL = '/host/auth/login/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# django-guardian
ANONYMOUS_USER_NAME = None

# for debug-toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

RUNSERVER_ON = 'trivia.localhost:8000'


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / config('STATIC_ROOT', default='static')

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
