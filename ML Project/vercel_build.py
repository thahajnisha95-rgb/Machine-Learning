"""Prepare Skillmatch during a Vercel build. Local runserver does not use this."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_PRODUCTION", "1")


def _is_postgres_url(value):
    value = (value or "").strip()
    return value.startswith("postgres://") or value.startswith("postgresql://")


def _migrate_database_url():
    for key in (
        "POSTGRES_URL_NON_POOLING",
        "DATABASE_URL_UNPOOLED",
        "DATABASE_URL",
        "POSTGRES_URL",
    ):
        value = (os.environ.get(key) or "").strip()
        if _is_postgres_url(value):
            return value
    return ""


migrate_url = _migrate_database_url()
if not _is_postgres_url(migrate_url):
    sys.exit(
        "Skillmatch needs DATABASE_URL on Vercel. Add Vercel Postgres, then redeploy."
    )
os.environ["DATABASE_URL"] = migrate_url
os.environ.pop("POSTGRES_URL", None)

if not (os.environ.get("DJANGO_SECRET_KEY") or "").strip():
    sys.exit("Set DJANGO_SECRET_KEY in the Vercel project environment.")

import django
from django.core.management import call_command

django.setup()
call_command("migrate", interactive=False)
call_command("seed_data")
call_command("train_recommender")
