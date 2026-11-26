from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from .models import Policy, PolicyConcept, PolicySchema


class PolicySchemaInline(admin.TabularInline):
    model = PolicySchema
    extra = 0
    autocomplete_fields = ('schema',)


class PolicyConceptForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The formset validates the concept against the schemas of the same
        # submission, so PolicyConcept.clean() must not query the database.
        self.instance.skip_schema_validation = True


class PolicyConceptFormSet(BaseInlineFormSet):
    schema_prefix = 'policyschema_set'

    def submitted_schema_ids(self):
        """Schemas of the policy as submitted in the PolicySchema inline."""
        ids = set()
        total = int(self.data.get(f'{self.schema_prefix}-TOTAL_FORMS') or 0)
        for index in range(total):
            if self.data.get(f'{self.schema_prefix}-{index}-DELETE'):
                continue
            value = self.data.get(f'{self.schema_prefix}-{index}-schema')
            if value and value.isdigit():
                ids.add(int(value))
        return ids

    def clean(self):
        super().clean()
        schema_ids = self.submitted_schema_ids()
        for form in self.forms:
            if not form.is_valid() or form.cleaned_data.get('DELETE'):
                continue
            concept = form.cleaned_data.get('concept')
            if concept and concept.schema_id not in schema_ids:
                form.add_error('concept', _('The concept schema is not associated with this policy.'))


class PolicyConceptInline(admin.TabularInline):
    model = PolicyConcept
    form = PolicyConceptForm
    formset = PolicyConceptFormSet
    extra = 0
    autocomplete_fields = ('concept',)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'approved', 'visible', 'creator', 'dateCreated', 'dateUpdated')
    list_filter = ('approved', 'visible')
    search_fields = ('name', 'description')
    ordering = ('-dateCreated',)
    date_hierarchy = 'start_date'
    autocomplete_fields = ('organisations', 'legislations')
    readonly_fields = ('creator', 'dateCreated', 'dateUpdated', 'totalAccesses', 'totalLikes', 'totalFollowers')
    inlines = (PolicySchemaInline, PolicyConceptInline)

    @admin.display(description=_('Year'))
    def year(self, obj):
        return obj.year()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'approved' in form.base_fields:
            form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)
