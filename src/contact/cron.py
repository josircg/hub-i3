from django.core import management
from django_cron import CronJobBase, Schedule


class SendNewsLetterCronJob(CronJobBase):
    """Sends queued newsletter every day"""
    RUN_EVERY_MINS = 24 * 60
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.send_newsletter'

    def do(self):
        management.call_command("send_newsletter", mass=True)
