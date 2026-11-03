from django.db.models import QuerySet
from django.utils import timezone
from utilities.managers import TranslationBaseQuerySet


def day_start():
    today = timezone.now().date()
    return today


class EventQuerySet(QuerySet):

    def approved_events(self):
        return self.filter(approved=True)

    def unapproved_events(self):
        return self.filter(approved=False)

    def upcoming_events(self):
        return self.filter(start_date__date__gt=day_start()). \
            order_by('-featured', 'start_date', 'end_date')

    def ongoing_events(self):
        return self.filter(start_date__date__lte=day_start(), end_date__date__gte=day_start()). \
            order_by('-featured', 'start_date', 'end_date')

    def past_events(self):
        return self.filter(end_date__date__lt=day_start()). \
            order_by('-featured', '-start_date', '-end_date')


class EventModeQuerySet(TranslationBaseQuerySet):
    default_field = 'description'
