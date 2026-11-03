from django.core import management
from django_cron import CronJobBase, Schedule


class UpdateVisaoCronJob(CronJobBase):
    RUN_EVERY_MINS = 5
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.update_visao'

    def do(self):
        management.call_command("populate_visao", update=True)
