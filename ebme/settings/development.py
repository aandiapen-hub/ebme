# ebme/settings/development.py
from dotenv import load_dotenv
import os

from .base import *

load_dotenv(os.path.join(BASE_DIR, '.env.development'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'FALSE') == 'True'

ALLOWED_HOSTS = ['127.0.0.0']

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        'ENGINE': os.getenv('DB_ENGINE'),
        'OPTIONS': {
            'options': os.getenv('DB_OPTIONS'),
            'sslmode': 'disable'
        },
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'TEST': {
            'MIGRATE': os.getenv('DB_TEST_MIGRATE', 'TRUE') == 'True',

        }
    }
}

