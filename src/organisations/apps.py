from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils.translation import gettext_lazy as _

from .signals import add_search_index, delete_search_index, notify_approved_organisation


class OrganisationsConfig(AppConfig):
    name = 'organisations'
    verbose_name = _('Organisations')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_organisation, 'organisations.Organisation',
                         dispatch_uid='notify_approved_organisation')
        post_save.connect(add_search_index, 'organisations.Organisation', dispatch_uid='organisation_add_searchindex')
        post_delete.connect(delete_search_index, 'organisations.Organisation',
                            dispatch_uid='organisation_delete_searchindex')
