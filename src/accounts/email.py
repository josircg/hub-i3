from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _, get_language
from eucs_platform import send_email
from eucs_platform.logger import log_message

from .tokens import account_activation_token


def send_activation_email(user, template):
    html_message = render_to_string(template, {
        'user': user,
        'domain': settings.DOMAIN,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    send_email(subject=_('Activate your account!'), to=[user.email], message=html_message)


def send_new_user_email(user):
    try:
        profile = user.profile

        with translation.override(profile.language):
            send_activation_email(user, f'accounts/emails/{profile.language}/acc_active_email.html')

        with translation.override(settings.LANGUAGE_CODE):
            notify_message = render_to_string(
                f'accounts/emails/{settings.LANGUAGE_CODE}/notify_new_user.html',
                {'user': user, 'site': settings.SITE_NAME}
            )

            send_email(subject=_('New user registration'), to=settings.EMAIL_RECIPIENT_LIST, message=notify_message)
    except Exception as e:
        log_message(user, f'send_new_user_email error: {e}')


def send_welcome_email(user):
    try:
        language = user.profile.language

        with translation.override(language):
            send_email(
                subject=_('Welcome!'),
                message=render_to_string(
                    f'accounts/emails/{language}/welcome_email.html',
                    {'user': user, "domain": settings.DOMAIN, 'reply_to': settings.EMAIL_CIVIS[0]}
                ),
                to=[user.email])
    except Exception as e:
        log_message(user, f'send_welcome_email error: {e}')


def send_password_reset_email(user):
    try:
        send_activation_email(user, f'accounts/emails/{get_language()}/acc-reactive.html')
    except Exception as e:
        log_message(user, f'send_password_reset_email error: {e}')
