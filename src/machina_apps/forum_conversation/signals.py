import copy
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from eucs_platform import send_email

logger = logging.getLogger("django.request")


def notify_flagged(sender, instance, **kwargs):
    """Notify flagged objects"""
    if instance.pk:
        from eucs_platform.logger import log_message
        verbose_name = sender._meta.verbose_name
        model = sender._meta.model_name
        old_instance = sender.objects.get(pk=instance.pk)

        if instance.flag and not old_instance.flag:
            try:
                to = copy.copy(settings.EMAIL_CIVIS)
                # Subject and notification message must be sent based on settings.LANGUAGE_CODE
                with translation.override(settings.LANGUAGE_CODE):
                    subject = _('%(name)s "%(description)s" has been flagged!') % {'name': verbose_name,
                                                                                   'description': str(instance)}
                # Templates must be a list, to raise exception if template for LANGUAGE_CODE does not exist.
                templates = ['emails/%s/notify_flagged.html' % settings.LANGUAGE_CODE]
                send_email(
                    subject=subject,
                    message=render_to_string(templates,
                                             {'name': str(instance), 'domain': settings.DOMAIN,
                                              'admin_url': reverse(f'admin:forum_conversation_{model}_change',
                                                                   args=[instance.pk])}),
                    to=to
                )
            except Exception as e:
                log_message(instance, f'send flag mail error: {e}')
                logger.exception(f'Error when trying to send {model} flag mail: {e}')
