from django.db import models
from django.utils.translation import gettext_lazy as _
from machina.apps.forum_conversation.abstract_models import AbstractTopic, AbstractPost
from rest_framework.reverse import reverse


class Topic(AbstractTopic):
    flag = models.BooleanField(verbose_name=_('Flagged'), default=False)


class Post(AbstractPost):
    flag = models.BooleanField(verbose_name=_('Flagged'), default=False)

    def get_absolute_url(self):
        return reverse(
            'forum_conversation:topic', (self.topic.forum.slug, self.topic.forum.pk, self.topic.slug, self.topic.pk)
        )


from machina.apps.forum_conversation.models import *  # noqa
