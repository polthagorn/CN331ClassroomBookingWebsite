#!/usr/bin/env bash
set -o errexit

# Install dependencies from repo root
python -m pip install --upgrade pip
pip install -r requirements.txt

# Go to the folder that contains manage.py
cd roombooking

# Static files + DB migrations
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Optional: create superuser via env vars (DJANGO_SUPERUSER_*)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
python manage.py shell << 'PY'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ["DJANGO_SUPERUSER_USERNAME"]
e = os.environ.get("DJANGO_SUPERUSER_EMAIL","")
p = os.environ["DJANGO_SUPERUSER_PASSWORD"]
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, e, p)
    print("Superuser created:", u)
else:
    print("Superuser already exists:", u)
PY
fi
