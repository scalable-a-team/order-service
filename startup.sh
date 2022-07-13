#!/bin/sh
set -e

python manage.py migrate

gunicorn --bind=0.0.0.0 --timeout 600 order_django.wsgi