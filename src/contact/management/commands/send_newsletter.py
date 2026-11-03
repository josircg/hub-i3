from contact.models import Newsletter, Subscriber
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.transaction import set_autocommit, commit
from eucs_platform.logger import log_message

User = get_user_model()


class Command(BaseCommand):
    label = 'Send all newsletters with status Ready'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--id', type=int, help='Newsletter ID')
        parser.add_argument('-m', '--mass', type=bool, help='Mass')

    def handle(self, *args, **options):
        if options['id']:
            dset = Newsletter.objects.filter(id=options['id'])
        else:
            dset = Newsletter.objects.filter(status=Newsletter.QUEUED)

        users = User.objects.filter(is_active=True)

        set_autocommit(False)
        for newsletter in dset:
            print('Iniciando envio')

            if newsletter.newsletter_type == '0':
                subscribers = Subscriber.objects.subscribers(newsletter)
            else:
                subscribers = users

            if not options['mass']:
                subscribers = subscribers[0:10]

            count = 0
            try:
                for subscriber in subscribers:
                    newsletter.send(subscriber)

                    if isinstance(subscriber, Subscriber):
                        subscriber.last_newsletter = newsletter
                        subscriber.save()

                    count += 1
                    print(subscriber.email)

                newsletter.status = Newsletter.SENT
                newsletter.sent_count += count
                newsletter.save()
                log_message(newsletter, f'Newsletter sent as type: {newsletter.get_newsletter_type_display()}')
                commit()
                print(f'Envio realizado para {count} contatos')

            except Exception as e:
                newsletter.status = Newsletter.ERROR
                newsletter.sent_count += count
                newsletter.save()
                log_message(newsletter, str(e))
                commit()
