from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from djoser import utils
from djoser.email import BaseEmailMessage

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


class LocalizedEmail(BaseEmailMessage):
    """Djoser e-mail rendered in the language preferred by the user."""

    template_file = None
    subject_text = None

    def get_language(self):
        """
        Return the user's preferred language.

        :return: Profile language, or settings.LANGUAGE_CODE when the user has no profile or an unknown language.
        """
        user = self.context.get('user')
        language = getattr(getattr(user, 'profile', None), 'language', None)
        if language not in dict(settings.TRANSLATED_LANGUAGES):
            language = settings.LANGUAGE_CODE
        return language

    def render(self):
        """Render the template of the user's language and set the subject translated to it."""
        language = self.get_language()
        self.template_name = f'accounts/emails/{language}/{self.template_file}'
        with translation.override(language):
            super().render()
            tag = getattr(settings, 'EMAIL_TAG', 'XXX')
            self.subject = f'[{tag}] {self.subject_text}'


class ActivationEmail(LocalizedEmail):
    template_file = 'acc_active_email.html'
    subject_text = _('Activate your account!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = context.get('user')
        context['uid'] = utils.encode_uid(user.pk)
        context['token'] = account_activation_token.make_token(user)
        context['domain'] = settings.DOMAIN
        return context


class ConfirmationEmail(LocalizedEmail):
    template_file = 'welcome_email.html'
    subject_text = _('Welcome!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain'] = settings.DOMAIN
        context['reply_to'] = settings.EMAIL_CIVIS[0]
        return context


class PasswordResetEmail(LocalizedEmail):
    template_file = 'password-reset-email.html'
    subject_text = _('Password reset')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = context.get('user')
        context['uid'] = utils.encode_uid(user.pk)
        context['token'] = default_token_generator.make_token(user)
        context['domain'] = settings.DOMAIN
        context['PASSWORD_RESET_TIMEOUT_HOURS'] = settings.PASSWORD_RESET_TIMEOUT // 3600
        return context
