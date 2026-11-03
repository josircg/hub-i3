from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet


class SubscriberQuerySet(QuerySet):

    def subscribe(self, name, email, opt_out=False, valid=False):
        try:
            subscriber = self.get(email=email)
            subscriber.opt_out = opt_out
        except ObjectDoesNotExist:
            subscriber = self.model(email=email, name=name, opt_out=opt_out, valid=valid)

        subscriber.save()

        return subscriber

    def subscribers(self, newsletter):
        """Returns active subscribers excluding the ones that received the last newsletter."""
        return self.filter(opt_out=False, valid=True).exclude(last_newsletter=newsletter)


class NewsletterQuerySet(QuerySet):

    def newsletters(self):
        """Return only itens marked as newsletters"""
        return self.filter(newsletter_type='0')
