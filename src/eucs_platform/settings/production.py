# In production set the environment variable like this:
#    DJANGO_SETTINGS_MODULE=eucs_platform.settings.production
from .base import *  # NOQA
import logging.config

# Strict password authentication and validation
# To use this setting, install the Argon2 password hashing algorithm.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Must mention ALLOWED_HOSTS in production!
# ALLOWED_HOSTS = ["eucs_platform.com"]

# Cache the templates in memory for speed-up
loaders = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
            "admin_tools.template_loaders.Loader",
        ],
    )
]

TEMPLATES[0]["OPTIONS"].update({"loaders": loaders})
TEMPLATES[0].update({"APP_DIRS": False})

# Hosts aceitos. Por padrão aceita qualquer um (comportamento anterior); em
# produção defina no local.env, ex.: ALLOWED_HOSTS=hub.exemplo.br,www.hub.exemplo.br
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# HTTPS. O site roda em HTTPS atrás do nginx, que deve enviar
# "X-Forwarded-Proto" (ver docs/nginx.conf). Em desenvolvimento local sem TLS,
# defina HTTPS_ONLY=False no local.env, senão o login/CSRF e o redirecionamento
# para https quebram no runserver.
HTTPS_ONLY = env.bool('HTTPS_ONLY', default=True)
if HTTPS_ONLY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Comece com 1 hora e aumente (ex.: 31536000) depois de validar o HTTPS.
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=3600)
    # O Django exige o esquema na origem. DOMAIN pode vir com ou sem "https://".
    _origin = DOMAIN if DOMAIN.startswith(('http://', 'https://')) else f'https://{DOMAIN}'
    CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[_origin])

# Define STATIC_ROOT for the collectstatic command
STATIC_ROOT = str(BASE_DIR.parent / "static")

# Log everything to the logs directory at the top
LOGFILE_ROOT = str(BASE_DIR.parent) + "/logs"

# Cron schedule on production only
CRON_CLASSES.extend(["contact.cron.SendNewsLetterCronJob", "accounts.cron.SendNotConfirmedUsersCronJob"])

# Reset logging
LOGGING_CONFIG = None
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue"
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": False
        },
        "proj_log_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOGFILE_ROOT + "/project.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "project": {
            "handlers": ["proj_log_file"],
            "level": "DEBUG"
        },
        "django.request": {
            "handlers": ["mail_admins", "console"],
            "propagate": True
        },
    },
}

logging.config.dictConfig(LOGGING)
