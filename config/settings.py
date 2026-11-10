import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-development-only-do-not-use-in-production')
if not DEBUG and SECRET_KEY == 'local-development-only-do-not-use-in-production':
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY before running in production.')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'portfolio.apps.PortfolioConfig',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True, 'OPTIONS': {'context_processors': [
        'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'
DATA_ROOT = Path(os.getenv('DATA_ROOT', str(BASE_DIR / 'data')))
DATA_ROOT.mkdir(parents=True, exist_ok=True)
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATA_ROOT / 'db.sqlite3', 'OPTIONS': {'timeout': 30}}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Private files have no public URL or development media route.
MEDIA_ROOT = Path(os.getenv('PRIVATE_MEDIA_ROOT', str(DATA_ROOT / 'private-media')))
MEDIA_URL = '/never-public/'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_TEMP_DIR = None
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_BYTES', '200000000'))
LOGIN_RATE_LIMIT = int(os.getenv('LOGIN_RATE_LIMIT', '5'))
LOGIN_RATE_WINDOW = int(os.getenv('LOGIN_RATE_WINDOW', '900'))
SIGNUP_RATE_LIMIT = int(os.getenv('SIGNUP_RATE_LIMIT', '5'))
SIGNUP_RATE_WINDOW = int(os.getenv('SIGNUP_RATE_WINDOW', '3600'))
UPLOAD_RATE_LIMIT = int(os.getenv('UPLOAD_RATE_LIMIT', '30'))
UPLOAD_RATE_WINDOW = int(os.getenv('UPLOAD_RATE_WINDOW', '3600'))
SUPPORT_RATE_LIMIT = int(os.getenv('SUPPORT_RATE_LIMIT', '5'))
SUPPORT_RATE_WINDOW = int(os.getenv('SUPPORT_RATE_WINDOW', '3600'))
HEALTHCHECK_MIN_FREE_BYTES = int(os.getenv('HEALTHCHECK_MIN_FREE_BYTES', str(100 * 1024 * 1024)))
CHECKOUT_RATE_LIMIT = int(os.getenv('CHECKOUT_RATE_LIMIT', '5'))
CHECKOUT_RATE_WINDOW = int(os.getenv('CHECKOUT_RATE_WINDOW', '900'))
PASSWORD_RESET_RATE_LIMIT = int(os.getenv('PASSWORD_RESET_RATE_LIMIT', '3'))
PASSWORD_RESET_RATE_WINDOW = int(os.getenv('PASSWORD_RESET_RATE_WINDOW', '3600'))
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '1') == '1'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
ZARINPAL_MERCHANT_ID = os.getenv('ZARINPAL_MERCHANT_ID', '')
ZARINPAL_SANDBOX = os.getenv('ZARINPAL_SANDBOX', '1') == '1'
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
if not DEBUG and ZARINPAL_MERCHANT_ID and not PUBLIC_BASE_URL.startswith('https://'):
    raise ImproperlyConfigured('PUBLIC_BASE_URL must use HTTPS in production.')
FILE_UPLOAD_HANDLERS = [
    'portfolio.uploads.BoundedUploadHandler',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
if os.getenv('TRUST_PROXY_HTTPS', '0') == '1':
    # Enable only behind a trusted proxy that overwrites this header.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if not DEBUG:
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
