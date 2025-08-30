FROM python:3.13-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY uv.lock pyproject.toml /app/

RUN pip3 install uv
RUN uv sync

COPY . .

ENV DJANGO_SETTINGS_MODULE "triviagame.settings"
ENV DJANGO_SECRET_KEY "this is a secret key for building purposes"

RUN uv run python manage.py collectstatic --noinput

CMD uv run daphne -b 0.0.0.0 -p 8080 triviagame.asgi:application