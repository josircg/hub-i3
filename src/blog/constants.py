from django.db import models
from django.utils.translation import gettext_lazy as _


class PostStatus(models.IntegerChoices):
    DRAFT = 0, _('Draft')
    PUBLISHED = 1, _('Published')


class PostSticky(models.IntegerChoices):
    NO = 0, _('No')
    YES = 1, _('Yes')
