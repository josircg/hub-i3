from django.apps import AppConfig
from django.db.models.signals import post_save, pre_save

from .signals import notify_new_dossier_curator, notify_dossier_object_moderation


class DossiersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dossiers'

    def ready(self):
        super().ready()
        post_save.connect(notify_new_dossier_curator, 'dossiers.DossierCurator',
                          dispatch_uid='notify_new_dossier_curator')
        pre_save.connect(notify_dossier_object_moderation, 'dossiers.DossierObject',
                         dispatch_uid='notify_dossier_object_moderation')
