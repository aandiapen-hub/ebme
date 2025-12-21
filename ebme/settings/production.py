# ebme/settings/production.py
from dotenv import load_dotenv
import os

from .base import *

load_dotenv(os.path.join(BASE_DIR, '.env.production'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'FALSE') == 'FALSE'
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

SECURE_HSTS_SECONDS = 31536000
#SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': os.getenv('DB_ENGINE'),
        'OPTIONS': {
                'options': os.getenv('DB_OPTIONS'),
                 'sslmode': 'require'
            },
        'NAME': os.getenv('DB_NAME'), 
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'), 
        'PORT': os.getenv('DB_PORT'),
        'TEST' : {
            'MIGRATE':os.getenv('DB_TEST_MIGRATE', 'TRUE') == 'True',
            
        }
    }
}
