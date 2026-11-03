from django.contrib import admin
from django.contrib.auth import get_user_model
from machina.apps.forum_permission.admin import UserForumPermissionAdmin as BaseUserForumPermissionAdmin, \
    UserForumPermission

USERNAME_FIELD = get_user_model().USERNAME_FIELD

admin.site.unregister(UserForumPermission)


@admin.register(UserForumPermission)  # noqa
class UserForumPermissionAdmin(BaseUserForumPermissionAdmin):
    search_fields = ('permission__codename', f'user__{USERNAME_FIELD}',)
