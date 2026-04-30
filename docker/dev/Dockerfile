FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    build-essential \
    libpoppler-cpp-dev \
    gcc \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install psycopg

ENV DJANGO_SETTINGS_MODULE=ebme.settings.development

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
