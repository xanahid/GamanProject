FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl gettext \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files at build time so whitenoise can serve them
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Daphne handles both HTTP and WebSockets (Channels)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
