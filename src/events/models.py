from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from utilities.models import AbstractTranslatedModel

from .managers import EventQuerySet, EventModeQuerySet


class EventMode(AbstractTranslatedModel):
    description = models.CharField(_('Description'), max_length=30)

    str_field = 'description'
    objects = EventModeQuerySet.as_manager()

    class Meta:
        verbose_name = _('Event Mode')
        verbose_name_plural = _('Event Modes')


class Event(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=3000)
    place = models.CharField(max_length=200, blank=True)
    start_date = models.DateTimeField(verbose_name=_('Start date'))
    end_date = models.DateTimeField(verbose_name=_('End date'))
    hour = models.TimeField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    featured = models.BooleanField(null=True, default=False)
    approved = models.BooleanField(verbose_name=_('Approved'), null=True)
    country = CountryField(null=True, blank=True)
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.LANGUAGES, null=True)
    mode = models.ForeignKey(EventMode, verbose_name=_('Type'), null=True, blank=True, on_delete=models.PROTECT)
    dossierobjects = GenericRelation('dossiers.DossierObject', related_query_name='event')

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ['start_date']
        verbose_name = _('Event')

    def __str__(self):
        return self.title

    def safe_url(self):
        return mark_safe(f'<a href="/editEvent/{self.id}" target="_blank">URL</a>')

    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    def save(self, *args, **kwargs):
        # approved can be null (not moderated), so we can't put self.approved = ... in one line
        if not self.pk and self.creator.is_staff:
            self.approved = True

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse_lazy('events')}?pk={self.pk}"
