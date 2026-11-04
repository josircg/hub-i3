from ckeditor.widgets import CKEditorWidget
from django.contrib import admin

from .models import Subscriber, Newsletter


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


admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
