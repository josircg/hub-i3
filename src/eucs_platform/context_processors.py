from django.conf import settings


def global_settings(request):
    return {
        'TRANSLATED_LANGUAGES': settings.TRANSLATED_LANGUAGES,
        'FEATURED_MGT': settings.FEATURED_MGT,
        'DOMAIN': settings.DOMAIN
    }
