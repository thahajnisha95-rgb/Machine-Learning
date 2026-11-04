"""Prepare Skillmatch during a Vercel build. Local runserver does not use this."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_PRODUCTION", "1")

if not os.environ.get("DATABASE_URL"):
    sys.exit(
        "Skillmatch needs DATABASE_URL on Vercel. Add Vercel Postgres, then redeploy."
    )
if not (os.environ.get("DJANGO_SECRET_KEY") or "").strip():
    sys.exit("Set DJANGO_SECRET_KEY in the Vercel project environment.")

import django
from django.core.management import call_command

django.setup()
call_command("migrate", interactive=False)
call_command("seed_data")
call_command("train_recommender")
