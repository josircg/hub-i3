from blog.models import Post
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from dossiers.models import Dossier
from projects.models import Project
from resources.models import Resource


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return ['home', 'about']

    def location(self, item):
        return reverse(item)


class ContentSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'


class ProjectSitemap(ContentSitemap):
    date_field = 'dateUpdated'

    def items(self):
        return Project.objects.approved().only('pk', 'dateUpdated')


class DossierSitemap(ContentSitemap):
    date_field = 'updated_on'

    def items(self):
        return Dossier.objects.approved_dossiers().only('pk', 'updated_on')


class BlogSitemap(ContentSitemap):
    date_field = 'updated_on'

    def items(self):
        return Post.objects.published().only('pk', 'updated_on', 'created_on', 'slug')


class ResourceSitemap(ContentSitemap):
    date_field = 'dateUpdated'

    def items(self):
        return Resource.objects.approved().only('pk', 'dateUpdated')


sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'dossiers': DossierSitemap,
    'blog_posts': BlogSitemap,
    'resources': ResourceSitemap,
}
