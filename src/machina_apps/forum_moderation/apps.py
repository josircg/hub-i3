from machina.apps.forum_moderation.apps import ForumModerationAppConfig as BaseForumModerationAppConfig


class ForumModerationAppConfig(BaseForumModerationAppConfig):
    name = 'machina_apps.forum_moderation'
    default = True
