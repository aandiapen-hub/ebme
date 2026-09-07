# tests/settings.py

SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django_htmx",
    "tests.testapp",
    "django_filter_table",
    "django_tables2",
    "django_filters",
    "django_bootstrap5",

]
MIDDLEWARE = [
    "django_htmx.middleware.HtmxMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

AUTH_USER_MODEL = "testapp.CustomUser"
DJANGO_TABLE= {
    'user_profile_model': "testapp.UserProfile",
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"


USE_TZ = True

