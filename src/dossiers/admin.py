from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.db import models
from django.shortcuts import render
from django.utils.translation import gettext as _

from .models import DossierCurator, DossierTranslation, DossierObject, Dossier
from .views import process_dossier_items


class DossierCuratorInline(admin.TabularInline):
    model = DossierCurator
    raw_id_fields = ('curator',)
    extra = 0


class DossierTranslationInline(admin.StackedInline):
    model = DossierTranslation
    extra = 0
    fields = (('language', 'title'), 'heading', 'content')
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='default')},
    }


class DossierObjectInline(admin.TabularInline):
    model = DossierObject
    extra = 0
    max_num = 0
    fields = ('ctype_name', 'content_object', 'order', 'approved')
    readonly_fields = ('ctype_name', 'content_object')
    ordering = ('content_type__app_label',)
    can_delete = False


class OrganisationInline(admin.TabularInline):
    model = Dossier.organisations.through
    extra = 0
    raw_id_fields = ('organisation',)
    verbose_name_plural = _('Partners')


class UserInline(admin.TabularInline):
    model = Dossier.users.through
    extra = 0
    raw_id_fields = ('user',)
    verbose_name_plural = _('Other collaborators')


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_filter = ('status',)
    list_display = ('title', 'dateCreated', 'status', 'curators')
    fields = ('title', 'heading', 'content', 'image', 'status', 'keywords', 'post')
    inlines = [
        DossierCuratorInline, DossierTranslationInline, OrganisationInline, UserInline, DossierObjectInline
    ]
    autocomplete_fields = ['keywords']
    raw_id_fields = ['post']
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='default')},
    }

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)

        if not change and formset.model == DossierCurator:
            form.instance.dossiercurator_set.update_or_create(curator=request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        if not change:
            process_dossier_items(request.user, form.instance)

    def response_change(self, request, obj):
        if "_preview" in request.POST:
            return render(request, "dossiers/dossier_detail.html", {'dossier': obj, 'preview': True})
        return super().response_change(request, obj)

    def get_view_on_site_url(self, obj=None):
        """Add link to views.DossierDetailView"""
        self.view_on_site = obj is not None and obj.status == Dossier.ACTIVE
        return super().get_view_on_site_url(obj)
