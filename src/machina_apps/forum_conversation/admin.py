from django.contrib import admin
from machina.apps.forum_conversation.admin import PostAdmin, TopicAdmin
from machina.core.db.models import get_model

Post = get_model('forum_conversation', 'Post')
Topic = get_model('forum_conversation', 'Topic')

admin.site.unregister([Post, Topic])


@admin.register(Post)
class CustomPostAdmin(PostAdmin):
    list_display = ('__str__', 'topic', 'poster', 'updated', 'approved', 'flag')
    list_filter = ('created', 'updated', 'flag')


@admin.register(Topic)
class CustomTopicAdmin(TopicAdmin):
    list_display = ('subject', 'forum', 'created', 'first_post', 'last_post', 'posts_count', 'approved', 'flag')
    list_filter = ('created', 'updated', 'flag')
