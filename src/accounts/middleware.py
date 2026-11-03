import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _, get_language
from eucs_platform import send_email
from eucs_platform.logger import log_message

User = get_user_model()
logger = logging.getLogger("django.request")


class BruteForceProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == settings.LOGIN_URL and request.method == 'POST':
            ip = self.get_client_ip(request)
            cache_key = f'bf_attempts_{ip}'
            attempts = cache.get(cache_key, 0)

            if attempts >= settings.BRUTE_FORCE_THRESHOLD:
                self.deactivate_user(request)
                return redirect(settings.LOGIN_URL)

            response = self.get_response(request)

            if response.status_code == 200:
                if attempts:
                    attempts = cache.incr(cache_key)
                else:
                    attempts = 1
                    cache.set(cache_key, attempts, timeout=settings.BRUTE_FORCE_TIMEOUT)

                if attempts >= settings.BRUTE_FORCE_THRESHOLD:
                    self.deactivate_user(request)
                    return redirect(settings.LOGIN_URL)

            return response
        else:
            return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def deactivate_user(self, request):
        try:
            username = request.POST.get('username')
            user = User.objects.get(**{User.USERNAME_FIELD: username})

            if user.is_active:
                user.is_active = False
                user.save()
                user_email = getattr(user, User.get_email_field_name())

                log_message(user, _('User blocked due to too many login attempts'))
                # Send reset password e-mail
                context = {
                    'token': default_token_generator.make_token(user),
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'PASSWORD_RESET_TIMEOUT_HOURS': settings.PASSWORD_RESET_TIMEOUT_DAYS * 24,
                    'domain': settings.DOMAIN,
                    'user': user
                }
                subject = _('Password Reset: User blocked due to too many login attempts')
                template = 'accounts/emails/%s/blocked-user-password-reset.html' % get_language()
                message = render_to_string(template, context)
                send_email(subject=subject, message=message, to=[user_email])
            else:
                # Send a warning to administrators
                logger.exception(_('Blocked user trying to login'), extra={'request': request})

            messages.warning(request, _('Too many login attempts. User has been blocked.'))
        except User.DoesNotExist:
            pass
