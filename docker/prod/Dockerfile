FROM python:3.13-slim

WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y \
    poppler-utils \
    build-essential \
    libpoppler-cpp-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput



ENV DJANGO_SETTINGS_MODULE=ebme.settings.production

CMD ["gunicorn", "ebme.wsgi:application", "--config", "docker/prod/gunicorn.conf.py"]
