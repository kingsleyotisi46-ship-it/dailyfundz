#!/usr/bin/env python
"""Create a production superuser using credentials supplied in the environment."""

import os

import django
from django.core.management.base import CommandError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from django.contrib.auth.models import User
from social.models import Wallet

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'support@dailyfundzboost.trade')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not password:
    raise CommandError('Set DJANGO_SUPERUSER_PASSWORD before running this script.')

if User.objects.filter(username=username).exists():
    raise CommandError(
        f'User {username!r} already exists; use the Django admin or createsuperuser command.'
    )

user = User.objects.create_superuser(
    username=username,
    email=email,
    password=password,
)
Wallet.objects.get_or_create(user=user)
print(f'Superuser {username!r} created.')
