from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse

from .constants import PostStatus, PostSticky
from .managers import PostQuerySet


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=1000, default='')
    image = models.ImageField(max_length=200)
    created_on = models.DateTimeField(auto_now_add=True)
    sticky = models.IntegerField(choices=PostSticky.choices, default=PostSticky.NO)
    status = models.IntegerField(choices=PostStatus.choices, default=PostStatus.DRAFT)
    dossierobjects = GenericRelation('dossiers.DossierObject', related_query_name='post')
    authors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='blog_posts')

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'post_detail', args=[
                self.created_on.year,
                self.created_on.strftime('%m'),
                self.created_on.strftime('%d'),
                self.slug])

    @property
    def safe_image(self):
        if self.image and default_storage.exists(self.image.path):
            return self.image
        else:
            return 'void_600.png'

    @property
    def published(self):
        return self.status == PostStatus.PUBLISHED

    @property
    def authors_names(self):
        """Returns a comma-separated list of author names, ignoring placeholder names like 'Empty user'"""
        return ', '.join(name for name in self.authors.values_list('name', flat=True) if name != 'Empty user')
