#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Optional: create superuser automatically (only if env vars set)
python manage.py createsuperuser \
  --username admin \
  --email "your@email.com" \
  --noinput || true

DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=your@email.com \
DJANGO_SUPERUSER_PASSWORD=admin1234 \
python manage.py createsuperuser --noinput || true
