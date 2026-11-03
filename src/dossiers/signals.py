import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext as _
from eucs_platform import send_email


def notify_new_dossier_curator(sender, instance, created, **kwargs):
    if created:
        try:
            curator = instance.curator
            language = curator.profile.language
            dossier_url = reverse_lazy('dossiers:dossier_detail', kwargs={'pk': instance.dossier.pk})
            dossier_edit_url = reverse_lazy('dossiers:dossier_edit', kwargs={'pk': instance.dossier.pk})

            with translation.override(language):
                send_email(
                    _('You are now the curator of the dossier %s!') % instance.dossier,
                    render_to_string(f'emails/{language}/new_curator.html',
                                     {'dossier_name': str(instance.dossier),
                                      'dossier_url': f'{settings.DOMAIN}{dossier_url}',
                                      'dossier_edit_url': f'{settings.DOMAIN}{dossier_edit_url}'}),
                    [curator.email]
                )
        except Exception as e:
            from eucs_platform.logger import log_message
            log_message(instance, f'Notify new dossier curator error: {e}')


def notify_dossier_object_moderation(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)

        if instance.creator_id and old_instance.approved is None:
            try:
                dossier = instance.dossier
                language = instance.creator.profile.language
                dossier_url = reverse_lazy('dossiers:dossier_detail', kwargs={'pk': dossier.pk})
                to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
                to.append(instance.creator.email)

                with translation.override(language):
                    send_email(
                        _('Content submitted to the dossier "%s"!') % instance.dossier,
                        render_to_string(f'emails/{language}/dossier_object_moderation.html',
                                         {'approved': instance.approved, 'dossier_name': str(instance.dossier),
                                          'dossier_url': f'{settings.DOMAIN}{dossier_url}'}),
                        to
                    )
            except Exception as e:
                from eucs_platform.logger import log_message
                log_message(instance, f'Notify dossier object moderation error: {e}')
