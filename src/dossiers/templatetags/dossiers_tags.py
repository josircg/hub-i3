from django.template import Library

register = Library()


def has_permission_to_edit(dossier, user):
    return user.is_active and (user.is_staff or dossier.dossiercurator_set.filter(curator=user).exists())


@register.simple_tag
def can_edit_dossier(user, dossier):
    return has_permission_to_edit(dossier, user)
