"""
Paste this file into PythonAnywhere: Web > WSGI configuration file.

Change PROJECT_HOME only if the repo lives in a different folder.
"""

import os
import sys

PROJECT_HOME = "/home/thagajunnisha/Machine-Learning/ML Project"

if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ["DJANGO_PRODUCTION"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
