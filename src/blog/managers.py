from django.db import models

from .constants import PostStatus


class PostQuerySet(models.QuerySet):

    def published(self):
        return self.filter(status=PostStatus.PUBLISHED)
