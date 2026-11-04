#!/usr/bin/env python
import os
import sys
import warnings

# drf-yasg e django-countries ainda importam pkg_resources (ver dívida técnica
# em .kiro/steering/django.md). Silencia o aviso até a migração para Django 4.x.
warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated", category=UserWarning
)

if __name__ == "__main__":
    # CHANGED manage.py will use development settings by
    # default. Change the DJANGO_SETTINGS_MODULE environment variable
    # for using the environment specific settings file.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "eucs_platform.settings.production"
    )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
