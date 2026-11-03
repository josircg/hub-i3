from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete

from .signals import add_search_index, delete_search_index


class BlogConfig(AppConfig):
    name = 'blog'

    def ready(self):
        super().ready()
        post_save.connect(add_search_index, 'blog.Post', dispatch_uid='blog_add_searchindex')
        post_delete.connect(delete_search_index, 'blog.Post', dispatch_uid='blog_delete_searchindex')
