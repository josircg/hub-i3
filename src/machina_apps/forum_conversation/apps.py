from django.db.models.signals import pre_save
from machina.apps.forum_conversation.apps import ForumConversationAppConfig as BaseForumConversationAppConfig

from .signals import notify_flagged


class ForumConversationAppConfig(BaseForumConversationAppConfig):
    name = 'machina_apps.forum_conversation'
    default = True

    def ready(self):
        super().ready()
        pre_save.connect(notify_flagged, 'forum_conversation.Topic', dispatch_uid='notify_flagged_topic')
        pre_save.connect(notify_flagged, 'forum_conversation.Post', dispatch_uid='notify_flagged_post')
