"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
project_path = str(BASE_DIR)
if project_path not in sys.path:
    sys.path.insert(0, project_path)

if os.environ.get("PYTHONANYWHERE_SITE") or os.environ.get("PYTHONANYWHERE_DOMAIN"):
    os.environ["DJANGO_PRODUCTION"] = "1"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
