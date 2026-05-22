"""
WSGI config for MorenaPOS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys

# Ensure the project root is in sys.path so that 'morenapos.settings' and
# submodules like 'core', 'ventas', etc. can be found when running from
# the Oryx build directory (e.g. /tmp/<build-id>/)
# This is needed because Oryx extracts the build to a temp directory
# and the project structure has morenapos/ as a subdirectory.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Also add the parent directory (project root) for when running from
# the root-level wsgi.py
_PARENT_DIR = os.path.dirname(_PROJECT_ROOT)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')

application = get_wsgi_application()
