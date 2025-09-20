#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

# Create superuser if not exists
python manage.py createsuperuser \
  --username admin \
  --email "your@email.com" \
  --noinput || true

# Set password for superuser
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.get_or_create(username="admin", defaults={"email": "your@email.com"})
u.set_password("yourpassword123")
u.save()
EOF

