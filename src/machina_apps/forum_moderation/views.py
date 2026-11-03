from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin, BaseDetailView
from machina.core.db.models import get_model
from machina.core.loading import get_class

Post = get_model('forum_conversation', 'Post')
Topic = get_model('forum_conversation', 'Topic')
PermissionRequiredMixin = get_class('forum_permission.viewmixins', 'PermissionRequiredMixin')


class BaseFlagView(PermissionRequiredMixin, SingleObjectTemplateResponseMixin, BaseDetailView):
    template_name = 'forum_moderation/flag_object.html'

    def flag(self, request, *args, **kwargs):
        """Flag the considered object and redirects the user to the success URL."""
        self.object = self.get_object()
        success_url = self.get_success_url()

        if self.object.flag:
            # force flag to False to send email after save as True
            self.object.flag = False
            self.object.save()

        self.object.flag = True
        self.object.save()
        messages.success(self.request, self.success_message)
        return redirect(success_url)

    def post(self, request, *args, **kwargs):
        """Handles POST requests."""
        return self.flag(request, *args, **kwargs)


class TopicFlagView(BaseFlagView):
    """Provides the ability to flag forum topics."""
    model = Topic
    success_message = _('This topic has been flagged successfully.')

    def get_context_data(self, **kwargs):
        """Returns the context data to provide to the template."""
        context = super().get_context_data(**kwargs)
        topic = self.get_object()
        context['forum'] = topic.forum
        context['topic'] = topic
        return context

    def get_success_url(self):
        """Returns the success URL to redirect the user to."""
        return reverse(
            'forum_conversation:topic',
            kwargs={
                'forum_slug': self.object.forum.slug,
                'forum_pk': self.object.forum.pk,
                'slug': self.object.slug,
                'pk': self.object.pk,
            },
        )


class PostFlagView(BaseFlagView):
    """Provides the ability to flag forum topics."""
    model = Post
    success_message = _('This post has been flagged successfully.')

    def get_context_data(self, **kwargs):
        """Returns the context data to provide to the template."""
        context = super().get_context_data(**kwargs)
        topic_post = self.get_object()
        context['forum'] = topic_post.topic.forum
        context['topic'] = topic_post.topic
        return context

    def get_success_url(self):
        """Returns the success URL to redirect the user to."""
        topic = self.object.topic
        return reverse(
            'forum_conversation:topic',
            kwargs={
                'forum_slug': topic.forum.slug,
                'forum_pk': topic.forum.pk,
                'slug': topic.slug,
                'pk': topic.pk,
            },
        )


from machina.apps.forum_moderation.views import *  # noqa
