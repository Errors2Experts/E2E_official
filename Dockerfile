FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --noinput && exec gunicorn errors2experts.wsgi:application --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile - --no-control-socket"]
