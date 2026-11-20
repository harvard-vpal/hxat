FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /hxat
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=hxat.settings.container

COPY hxat/requirements hxat/requirements
RUN pip install --no-cache-dir uv==0.13.7 \
    && uv pip install --system --no-cache -r hxat/requirements/container.txt

COPY . .

# health.txt is a target for load balancer health checks. WhiteNoise serves it from STATIC_ROOT.
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && printf 'ok\n' > http_static/health.txt

# gunicorn writes under the user's home.
RUN useradd --system --create-home hxat
USER hxat

EXPOSE 8000
# docker-compose.yml replaces this command to run migrations and the development server.
CMD ["gunicorn", "hxat.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "60", "--access-logfile", "-"]
