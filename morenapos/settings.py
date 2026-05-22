"""
Configuración para MorenaPOS.
Usa variables de entorno para datos sensibles (producción).
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# APIPERU token para consulta de DNI/RUC
APIPERU_TOKEN = os.environ.get('APIPERU_TOKEN', '2bb538e5198295b0f3b7f1a6552df46a640fb362f9f8075dce3820a991ffef3f')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG forzado a True para diagnosticar el error 500 en Azure
# TODO: Cambiar a False cuando el error esté resuelto
DEBUG = True

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'morenapos.azurewebsites.net,pos.tradicionlamorena.com').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'django_htmx',
    # 'django_q',  # Comentado temporalmente debido a problemas de dependencias
    'corsheaders',
    
    # Local apps
    'core',
    'ventas',
    'facturacion',
    'mesas',
]

# Custom user model
AUTH_USER_MODEL = 'core.Usuario'

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
    'django_htmx.middleware.HtmxMiddleware',
]

# Solo agregar debug_toolbar si está instalado y DEBUG=True
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    except ImportError:
        pass

ROOT_URLCONF = 'morenapos.urls'

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
                'core.context_processors.sede_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'morenapos.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# Usa variables de entorno para producción en Azure
DB_ENGINE = os.environ.get('DB_ENGINE', 'mssql')

if DB_ENGINE == 'sqlite':
    # Fallback a SQLite para pruebas locales sin SQL Server
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif DB_ENGINE == 'mssql':
    # SQL Server (Azure SQL Database)
    # Usa mssql-django con ODBC Driver
    # Azure App Service Linux tiene ODBC Driver 17 pre-instalado
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': os.environ.get('DB_NAME', 'morena'),
            'USER': os.environ.get('DB_USER', 'morena159'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'ZjIckH82e'),
            'HOST': os.environ.get('DB_HOST', 'morena.database.windows.net'),
            'PORT': os.environ.get('DB_PORT', '1433'),
            'OPTIONS': {
                'driver': os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
                'extra_params': 'TrustServerCertificate=yes;Encrypt=yes',
            },
        }
    }
else:
    # PostgreSQL u otro
    DATABASES = {
        'default': {
            'ENGINE': f'django.db.backends.{DB_ENGINE}',
            'NAME': os.environ.get('DB_NAME', 'morena'),
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', ''),
        }
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

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/caja/'
LOGOUT_REDIRECT_URL = '/login/'

# Django Q2 configuration for async tasks
Q_CLUSTER = {
    'name': 'morenapos',
    'workers': 2,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': os.environ.get('REDIS_HOST', '127.0.0.1'),
        'port': int(os.environ.get('REDIS_PORT', '6379')),
        'db': 0,
        'password': os.environ.get('REDIS_PASSWORD', None),
        'socket_timeout': 5,
        'retry_on_timeout': True,
    }
}

# CORS settings
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Security settings for production
# Azure App Service termina SSL en el frontend (load balancer)
# Django necesita saber que está detrás de un proxy de confianza
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL', 'False').lower() in ('true', '1')
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_SECURE', 'False').lower() in ('true', '1')
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_SECURE', 'False').lower() in ('true', '1')

# Logging configuration for Azure (captura errores en stderr)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'morenapos-cache',
    }
}

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_VIEW = 'core.views.rate_limit_exceeded'

# Whitenoise - compresión y caching de archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
