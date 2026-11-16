from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils.translation import gettext_lazy as _

from .signals import add_search_index, delete_search_index, notify_approved_event


class EventsConfig(AppConfig):
    name = 'events'
    verbose_name = _('Events')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_event, 'events.Event', dispatch_uid='notify_approved_event')
        post_save.connect(add_search_index, 'events.Event', dispatch_uid='event_add_searchindex')
        post_delete.connect(delete_search_index, 'events.Event', dispatch_uid='event_delete_searchindex')
