from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils.translation import ugettext_lazy as _

from .signals import add_search_index, delete_search_index, notify_approved_resource


class ResourcesConfig(AppConfig):
    name = 'resources'
    verbose_name = _('Resources')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_resource, 'resources.Resource', dispatch_uid='notify_approved_resource')
        pre_save.connect(notify_approved_resource, 'resources.TrainingResource',
                         dispatch_uid='notify_approved_training_resource')
        post_save.connect(add_search_index, 'resources.Resource', dispatch_uid='resource_add_searchindex')
        post_delete.connect(delete_search_index, 'resources.Resource', dispatch_uid='resource_delete_searchindex')
        post_save.connect(add_search_index, 'resources.TrainingResource',
                          dispatch_uid='trainingresource_add_searchindex')
        post_delete.connect(delete_search_index, 'resources.TrainingResource',
                            dispatch_uid='trainingresource_delete_searchindex')
