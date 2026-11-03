import copy
import mimetypes
import os
from io import BytesIO

from PIL import Image
from ckeditor.widgets import CKEditorWidget
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import ADDITION
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from eucs_platform import send_email
from eucs_platform.logger import log_message
from machina.apps.forum.models import Forum

from .models import ForumProposal, Subscriber, Newsletter


class SubscriberAdmin(admin.ModelAdmin):
    list_filter = ('valid', 'opt_out')
    search_fields = ('name', 'email', 'organisation')
    list_display = ('name', 'email', 'valid', 'opt_out', 'organisation', 'dateCreated',)
    exclude = ('last_newsletter',)


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'dateCreated', 'status', 'newsletter_type')
    readonly_fields = ('status', 'sent_count', 'read_count')
    autocomplete_fields = ('blog', 'featured_resource')

    def get_view_on_site_url(self, obj=None):
        self.view_on_site = obj and obj.html
        return super().get_view_on_site_url(obj)

    def save_model(self, request, obj, form, change):
        if '_queued' in request.POST:
            obj.status = Newsletter.QUEUED

        super().save_model(request, obj, form, change)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # Status that enable mark newsletter as queued
        context['status_allows_sending'] = [Newsletter.DRAFT, Newsletter.READY, Newsletter.ERROR]
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['featured_text'].widget = CKEditorWidget(config_name='frontpage')
        return form


@admin.register(ForumProposal)
class ForumProposalAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'creator', 'approved')
    fields = ('name', 'description', 'image', 'creator', 'approved')
    readonly_fields = ('name', 'image', 'creator')
    list_filter = ('approved',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        form.base_fields['description'].widget = CKEditorWidget(config_name='frontpage')
        return form

    def save_model(self, request, obj, form, change):
        if change:
            old_instance = self.model.objects.get(pk=obj.pk)

            if obj.approved and old_instance.approved != obj.approved:

                forum = Forum(name=obj.name, description=obj.description, type=0)

                try:
                    # Point to default forum category
                    with translation.override(settings.LANGUAGE_CODE):
                        parent_name = _('Community Forums')

                    parent = Forum.objects.get(name=parent_name, type=1)
                    forum.parent = parent
                except Forum.DoesNotExist:
                    pass

                if obj.image and default_storage.exists(obj.image.path):
                    # Create a new image. We can't share images between instances (django-cleanup limitation).
                    img_name = os.path.basename(obj.image.name)
                    image = Image.open(obj.image.path)
                    buffer = BytesIO()
                    image.save(buffer, format=image.format)
                    mimetype = mimetypes.guess_type(img_name)[0]
                    image_file = InMemoryUploadedFile(buffer, None, img_name, mimetype, buffer.tell(), None)
                    forum.image = image_file

                forum.save()

                log_message(forum, _('Forum proposal created'), request.user, ADDITION)

                with translation.override(settings.LANGUAGE_CODE):
                    subject = _('Your forum "%s" has been created!') % forum.name

                templates = ['emails/%s/forum_created.html' % settings.LANGUAGE_CODE]
                forum_url = reverse('forum:forum', kwargs={'slug': forum.slug, 'pk': forum.pk})
                message = render_to_string(templates, {
                    'forum': forum.name, 'forum_url': f'{settings.DOMAIN}{forum_url}'
                })

                to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
                to.append(obj.creator.email)

                send_email(subject=subject, message=message, to=to)

        super().save_model(request, obj, form, change)


admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
