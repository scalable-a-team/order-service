#!/bin/sh
set -e

python manage.py migrate

opentelemetry-instrument gunicorn order_django.wsgi -c gunicorn.config.py --bind=0.0.0.0 --reload --timeout 600