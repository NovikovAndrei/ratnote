# rat_notebook/settings.py
import os
from pathlib import Path

# --- Базовые пути ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Аутентификация / редиректы ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# --- Безопасность / окружение ---
# В проде лучше брать из переменной окружения:
# SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-unsafe-key')
SECRET_KEY = 'django-insecure-4(3&#f=oj+wc027ka34l8b@%%i#3kaibm7gvji7izl=6*7ra)1'

DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'

# Всегда держим локальные хосты + твои домены
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ratnote.pythonanywhere.com',
    'ratnote.ru',
    'www.ratnote.ru',
]

# Для безопасных POST/COOKIE с прод-доменов/https
CSRF_TRUSTED_ORIGINS = [
    'https://ratnote.pythonanywhere.com',
    'https://ratnote.ru',
    'https://www.ratnote.ru',
]

# --- Приложения ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'results',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rat_notebook.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rat_notebook.wsgi.application'

# --- База данных ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Валидаторы пароля ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Локализация ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Статика ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']          # твои исходники статики
STATIC_ROOT = BASE_DIR / 'staticfiles'            # сюда collectstatic собирает

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
