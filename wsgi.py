"""
WSGI config for MorenaPOS - Root level for Oryx detection.

Oryx (Azure App Service build system) looks for a wsgi.py file at the
project root to auto-detect Django. This file re-exports the application
from morenapos.wsgi so Oryx can find it.

Oryx then generates a gunicorn command like:
    gunicorn --bind=0.0.0.0:8000 --timeout=600 wsgi:application
"""

import os
import sys

# Add the project root and morenapos directory to sys.path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_MORENAPOS_DIR = os.path.join(_PROJECT_ROOT, 'morenapos')
if _MORENAPOS_DIR not in sys.path:
    sys.path.insert(0, _MORENAPOS_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')

# Import the actual application from morenapos.wsgi
from morenapos.wsgi import application
