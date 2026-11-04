"""
WSGI config for eucs_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
import os
import warnings

# drf-yasg e django-countries ainda importam pkg_resources (ver dívida técnica
# em .kiro/steering/django.md). Silencia o aviso até a migração para Django 4.x.
warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated", category=UserWarning
)

from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "eucs_platform.settings.production"
)

application = get_wsgi_application()

# Wrap werkzeug debugger if DEBUG is on
if settings.DEBUG:
    try:
        import django.views.debug
        import six
        from werkzeug.debug import DebuggedApplication

        def null_technical_500_response(request, exc_type, exc_value, tb):
            six.reraise(exc_type, exc_value, tb)

        django.views.debug.technical_500_response = null_technical_500_response
        application = DebuggedApplication(
            application,
            evalex=True,
            # Turning off pin security as DEBUG is True
            pin_security=False,
        )
    except ImportError:
        pass
