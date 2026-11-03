from django.urls import path
from machina.apps.forum_moderation.urls import \
    ForumModerationURLPatternsFactory as BaseForumModerationURLPatternsFactory
from machina.core.loading import get_class


class ForumModerationURLPatternsFactory(BaseForumModerationURLPatternsFactory):
    topic_flag_view = get_class('forum_moderation.views', 'TopicFlagView')
    post_flag_view = get_class('forum_moderation.views', 'PostFlagView')

    def get_urlpatterns(self):
        url_patterns = super().get_urlpatterns()
        return url_patterns + [
            path('topic/<str:slug>-<int:pk>/flag/', self.topic_flag_view.as_view(), name='topic_flag', ),
            path(
                'topic/<str:topic_slug>-<int:topic_pk>/<int:pk>/post/flag/', self.post_flag_view.as_view(),
                name='post_flag',
            ),
        ]


urlpatterns_factory = ForumModerationURLPatternsFactory()
