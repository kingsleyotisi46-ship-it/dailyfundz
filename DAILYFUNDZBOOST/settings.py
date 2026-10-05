"""
Django settings for DAILYFUNDZBOOST project.

Project settings for the supported Django 6.x runtime.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('SECRET_KEY must be configured when DEBUG is False.')
    SECRET_KEY = 'django-insecure-dev-only-change-in-production'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Site URL for email links
SITE_URL = os.environ.get('SITE_URL', 'https://dailyfundzboost-cwo5.onrender.com')

# CSRF trusted origins for custom domains
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', SITE_URL).split(',')
    if origin.strip()
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'cloudinary_storage',
    'cloudinary',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'social',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DAILYFUNDZBOOST.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'DAILYFUNDZBOOST.wsgi.application'


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL and not DEBUG:
    raise ImproperlyConfigured('DATABASE_URL must be configured when DEBUG is False.')

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}' if DEBUG else None,
        conn_max_age=600
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Configuration (for persistent media storage on Render)
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
    }
else:
    CLOUDINARY_STORAGE = {}

STORAGES = {
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.MediaCloudinaryStorage'
            if CLOUDINARY_URL
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Login redirect
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'main_panel'
LOGOUT_REDIRECT_URL = 'home'

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Add production frontend URL
RENDER_FRONTEND_URL = os.environ.get('RENDER_FRONTEND_URL')
if RENDER_FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(RENDER_FRONTEND_URL)

# Allow all origins in development
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# SMM Provider Settings - JustAnotherPanel
SMM_PROVIDER_URL = os.environ.get('SMM_PROVIDER_URL', 'https://justanotherpanel.com/api/v2')
SMM_PROVIDER_KEY = os.environ.get('SMM_PROVIDER_KEY', '')  # Must be set in environment

# GrizzlySMS Settings
GRIZZLY_API_KEY = os.environ.get('GRIZZLY_API_KEY', '')

# Email Configuration - Zoho Mail SMTP
# Use console backend in development if no password set, SMTP in production
_email_password = os.environ.get('EMAIL_HOST_PASSWORD', '')
if _email_password or not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # Console backend for development - emails print to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Zoho Mail SMTP settings
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.zoho.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'noreply@dailyfundzboost.trade')
EMAIL_HOST_PASSWORD = _email_password  # Zoho App password
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'DAILYFUNDZBOOST <noreply@dailyfundzboost.trade>')

# Admin notification email
ADMIN_NOTIFICATION_EMAIL = os.environ.get(
    'ADMIN_NOTIFICATION_EMAIL',
    'support@dailyfundzboost.trade',
)

# Password Reset Settings
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

# Company Info
COMPANY_NAME = 'DAILYFUNDZBOOST'
COMPANY_EMAIL = 'support@dailyfundzboost.trade'
NOREPLY_EMAIL = 'noreply@dailyfundzboost.trade'
COMPANY_WHATSAPP = '+2348105594678'
OPAY_ACCOUNT = '9070910294'
