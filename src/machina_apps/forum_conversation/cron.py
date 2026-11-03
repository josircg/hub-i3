from datetime import timezone, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_cron import CronJobBase, Schedule

User = get_user_model()


class NewForumResponseCronJob(CronJobBase):
    RUN_EVERY_MINS = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.new_forum_response_cron_job'

    def do(self):
        from machina.core.db.models import get_model
        Forum = get_model('forum', 'Forum')
        Topic = get_model('forum_conversation', 'Topic')
        Post = get_model('forum_conversation', 'Post')

        this_hour = timezone.now()
        one_hour_before = this_hour + timedelta(minutes=-2)
        topics = Topic.objects.get_queryset().filter(status=0).filter(updated__range=(one_hour_before, this_hour))
        for topic in topics:
            owner = topic.poster_id
            user = User.objects.get(pk=owner)

            # Send email to owner
            mail_subject = 'Nova mensagem no Fórum'
            slug = '' + topic.slug + '-' + str(topic.id)
            forum = get_object_or_404(Forum, id=topic.forum_id)
            forum_slug = forum.slug + '-' + str(forum.id)
            message = render_to_string('forum_emails/forum_answer.html',
                                       {'topic': topic, 'slug': slug, 'forum': forum_slug, "domain": settings.HOST})
            to_email = user.email
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.content_subtype = "html"
            email.send()
            print("email sent to" + str(to_email))

            users = User.objects.get_queryset().filter(~Q(pk=owner))

            for user in users:
                isSubscripted = topic in user.topic_subscriptions.all()
                if isSubscripted:
                    # Send email to subscriber
                    posts = Post.objects.get_queryset().filter(topic_id=topic.id,
                                                               updated__range=(one_hour_before, this_hour))
                    for post in posts:
                        if user.id is not post.poster_id:
                            mail_subject = 'Nova mensagem no Fórum'
                            slug = '' + topic.slug + '-' + str(topic.id)
                            forum = get_object_or_404(Forum, id=topic.forum_id)
                            forum_slug = forum.slug + '-' + str(forum.id)
                            message = render_to_string('forum_emails/forum_subscription_new_message.html',
                                                       {'topic': topic, 'slug': slug, 'forum': forum_slug,
                                                        "domain": settings.HOST})
                            to_email = user.email
                            email = EmailMessage(
                                mail_subject, message, to=[to_email]
                            )
                            email.content_subtype = "html"
                            email.send()
                        else:
                            print("Do not send email")
