# tests/settings.py

SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "tests.testapp",
    "django_filter_table",
]

AUTH_USER_MODEL = "testapp.CustomUser"
DJANGO_TABLE= { 'user_profile_model': "testapp.UserProfile" }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    },
]

USE_TZ = True

