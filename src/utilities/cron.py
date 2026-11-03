from django.core import management
from django_cron import CronJobBase, Schedule


class CleanExpiredCaptchaCronJob(CronJobBase):
    """Clean expired captcha every day"""
    RUN_EVERY_MINS = 24 * 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.clean_expired_captcha'

    def do(self):
        management.call_command("captcha_clean")


class ClearSessions(CronJobBase):
    """Clear sessions expired every day"""
    RUN_EVERY_MINS = 24 * 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'django.clearsessions'

    def do(self):
        management.call_command("clearsessions", verbosity=2)
