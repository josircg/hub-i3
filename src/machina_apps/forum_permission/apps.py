from machina.apps.forum_permission.apps import ForumPermissionAppConfig as BaseForumPermissionAppConfig


class ForumPermissionAppConfig(BaseForumPermissionAppConfig):
    name = 'machina_apps.forum_permission'
    default = True
