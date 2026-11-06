import os
from django.core.exceptions import ImproperlyConfigured

from .settings import *


def required_setting(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'The {name} environment variable is required.')
    return value


SECRET_KEY = required_setting('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in required_setting('ALLOWED_HOSTS').split(',')
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS must contain at least one host.')
ALLOWED_HOSTS.append('127.0.0.1')
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in required_setting('CSRF_TRUSTED_ORIGINS').split(',')
    if origin.strip()
]
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS must contain at least one origin.')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/gaap.sqlite3',
    }
}

MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    },
}
