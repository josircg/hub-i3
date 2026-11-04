from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .managers import DossierObjectQuerySet, DossierCuratorQuerySet, DossierQuerySet


def get_content_type(content_type, content_object):
    """Helper function to return content_type"""
    ctype = content_type
    # Resource objects can be TrainingResource, but resources.views uses Resource.isTrainingResource instead of the
    # TrainingResource model (we can't save TrainingResource ContentType to DossierObject because of this behavior).
    # Changing this behavior is complex, so it's better to resolve the content_type in this helper function and
    # return the correct object to display the content_type name.
    if content_type.model == 'resource':
        if content_object.isTrainingResource:
            ctype = ContentType.objects.get_for_model(
                django_apps.get_model('resources', 'TrainingResource'), for_concrete_model=False
            )

    return ctype


class Dossier(models.Model):
    DRAFT = 'D'
    ACTIVE = 'A'
    INACTIVE = 'I'
    STATUS = (
        (DRAFT, _("Draft")),
        (ACTIVE, _("Published")),
        (INACTIVE, _("Not Published"))
    )
    title = models.CharField(verbose_name=_('Title'), max_length=200, unique=True,
                             help_text=_('Please write the title or name of the dossier.'))
    heading = models.TextField(verbose_name=_('Summary'), blank=True, null=True,
                               help_text=_('Briefly explain the dossier (max 300 characters).'))
    content = models.TextField(verbose_name=_('Description'), blank=True, null=True,
                               help_text=_('Describe what the dossier is about, its title/theme, objectives, context '
                                           'and other relevant aspects (max 200 words).'))
    image = models.ImageField(verbose_name=_('Image for the dossier header'), max_length=200, blank=True, null=True,
                              help_text=_('The image (.jpg or .png) will be displayed at 320x290 pixels and 1320x300 '
                                          'pixels, and may be cropped.'))
    status = models.CharField(verbose_name=('Status'), max_length=1, choices=STATUS, default=DRAFT)
    dateCreated = models.DateTimeField(verbose_name=_('Created date'), auto_now_add=True)
    updated_on = models.DateTimeField(verbose_name=_('Updated date'), auto_now=True)
    keywords = models.ManyToManyField('utilities.Keyword', verbose_name=_('Keywords'), blank=True,
                                      help_text=_('Please select or add 2-3 keywords <b>separated by commas or by '
                                                  'pressing enter</b>. These keywords automatically associate content '
                                                  'registered in Cívis with the dossier. <b>DO NOT</b> include the '
                                                  'expression \'citizen science\' as a keyword.'))
    post = models.ForeignKey('blog.Post', verbose_name=_('Call to action'), related_name='dossiers',
                             on_delete=models.PROTECT, null=True, blank=True)
    organisations = models.ManyToManyField('organisations.Organisation', verbose_name=_('Partners'), blank=True,
                                           limit_choices_to={'approved': True})
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Other collaborators'), blank=True,
                                   limit_choices_to={'is_active': True})

    objects = DossierQuerySet.as_manager()

    class Meta:
        verbose_name = _('Dossier')
        verbose_name_plural = _('Dossiers')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('dossiers:dossier_detail', args=(self.id,))

    @property
    def is_active(self):
        return self.status == self.ACTIVE

    @property
    def is_draft(self):
        return self.status == self.DRAFT

    @property
    @admin.display(description=_('Curators'))
    def curators(self):
        return ', '.join(self.dossiercurator_set.values_list('curator__name', flat=True))

    @property
    def translated_data(self):
        """
        Returns the translation object for the current active language or the
        instance itself as a fallback.

        This property provides a unified interface to access translated fields
        (title, heading, content) without manually checking for the existence
        of a DossierTranslation record in templates.

        IMPORTANT: To avoid N+1 performance issues, always use this property
        in conjunction with the `with_translations()` method from
        DossierQuerySet. That method performs a specialized `prefetch_related`
        filtered by the current language.

        Usage in templates:
            {{ dossier.translated_data.title }}
        """
        translations = getattr(self, 'current_translation', None)

        if translations:
            return translations[0]

        return self


class DossierCurator(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE)
    curator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Curator'), on_delete=models.PROTECT)

    objects = DossierCuratorQuerySet.as_manager()

    class Meta:
        unique_together = ('dossier', 'curator')
        verbose_name = _('Dossier Curator')
        verbose_name_plural = _('Dossier Curators')

    def __str__(self):
        return f'{self.curator}'


class DossierObject(models.Model):
    dossier = models.ForeignKey(Dossier, verbose_name=_('Dossier'), on_delete=models.CASCADE)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    order = models.PositiveIntegerField(verbose_name=_('Order'))
    # DossierObject will not be deleted, not approved will be disabled and became invisible until
    # user rebuild item assignment.
    approved = models.BooleanField(
        verbose_name=_('Approved'), default=None, null=True, blank=True,
        choices=((None, _('Not moderated')), (True, _('Approved')), (False, _('Not approved')))
    )
    # User who indicated the content to the dossier
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Creator'), on_delete=models.PROTECT,
                                null=True)

    objects = DossierObjectQuerySet.as_manager()

    class Meta:
        verbose_name = _('Dossier Object')
        verbose_name_plural = _('Dossier Objects')
        unique_together = ('dossier', 'content_type', 'object_id')

    def __str__(self):
        return f'{self.content_type} {self.content_object}'

    @property
    @admin.display(description=_('content type'))
    def ctype_name(self):
        """
        Returns a custom name for the content type based on specific business rules:
        - 'blog.post' is displayed as 'Blog'
        - 'resources.resource' with isTrainingResource=True is displayed as 'Training Resource'
        Otherwise, returns the default content type name.
        """
        model_name = '.'.join(self.content_type.natural_key()).lower()
        # Basic mapping without extra conditions
        basic_map = {
            'blog.post': _('Blog'),
        }
        # Conditional mapping based on content_object attributes
        if model_name == 'resources.resource' and self.content_object.isTrainingResource:
            return _('Training Resource')

        return basic_map.get(model_name, self.content_type.name)


class DossierTranslation(models.Model):
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE)
    language = models.CharField(max_length=5, choices=settings.TRANSLATED_LANGUAGES, verbose_name=_('Language'))
    title = models.CharField(max_length=200)
    heading = models.TextField()
    content = models.TextField()

    class Meta:
        unique_together = (('dossier', 'language'), ('language', 'title'))

    def __str__(self):
        return f'{self.language} {self.title}'
