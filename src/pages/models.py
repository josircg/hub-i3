from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import SectionQuerySet, ArticleQuerySet


class Page(models.Model):
    slug = models.SlugField()
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)

    class Meta:
        verbose_name = _('Page')
        verbose_name_plural = _('Pages')
        constraints = [
            models.UniqueConstraint(fields=['slug', 'language'], name='unique_page_slug_language'),
        ]

    def __str__(self):
        return self.title


class Section(models.Model):
    page = models.ForeignKey(Page, verbose_name=_('Page'), on_delete=models.PROTECT, related_name='sections', null=True,
                             blank=True)
    order = models.PositiveIntegerField(verbose_name=_('Order'))
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)

    objects = SectionQuerySet.as_manager()

    class Meta:
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.page_id:
            self.language = self.page.language

        super().save(*args, **kwargs)


class Article(models.Model):
    section = models.ForeignKey(Section, verbose_name=_('Section'), on_delete=models.PROTECT, related_name='articles',
                                null=True, blank=True)
    order = models.PositiveIntegerField(verbose_name=_('Order'))
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    description = models.TextField(verbose_name=_('Description'))
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.section_id:
            self.language = self.section.language

        super().save(*args, **kwargs)
