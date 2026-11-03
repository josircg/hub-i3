from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import engines
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _, ngettext
from django_cron import CronJobBase, Schedule
from eucs_platform import send_email

User = get_user_model()


class SendNotConfirmedUsersCronJob(CronJobBase):
    RUN_EVERY_MINS = 24 * 60
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.send_not_confirmed_users'

    def do(self):
        counter = User.objects.filter(last_login__isnull=True, is_active=False).count()

        engine = engines['django']

        template = engine.from_string(
            '<html>'
            '<body>'
            '<a href="{{ user_changelist|escape }}">{{ msg }}</a>'
            '</body>'
            '</html>'
        )

        query = urlencode({'last_login__isnull': True, 'is_active': False})
        user_changelist = f'{settings.DOMAIN}{reverse_lazy("admin:authtools_user_changelist")}?{query}'

        msg = ngettext(
            'There is %d user who has not yet confirmed their registration.',
            'There are %d users who have not yet confirmed their registration.',
            counter
        ) % counter

        send_email(
            _('Users without registration confirmation'),
            template.render({'user_changelist': user_changelist, 'msg': msg}),
            settings.EMAIL_CIVIS
        )
