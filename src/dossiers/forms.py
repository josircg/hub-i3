from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django_select2.forms import ModelSelect2MultipleWidget
from utilities.widgets import KeywordsSelect2TagWidget

from .models import Dossier, DossierObject


class DossierForm(forms.ModelForm):
    class Meta:
        model = Dossier
        fields = ('title', 'heading', 'content', 'image', 'status', 'keywords')
        widgets = {
            'keywords': KeywordsSelect2TagWidget,
            'heading': CKEditorWidget(config_name='frontpage'),
            'content': CKEditorWidget(config_name='default'),
            'image': forms.FileInput
        }
        labels = {
            'image': '',
        }


# FormSet to perform DossierObject moderation
DossierObjectFormSet = inlineformset_factory(
    Dossier, DossierObject, fields=('id', 'approved'), extra=0, can_delete=False, max_num=0,
    labels={'approved': ''}
)


class DossierSelectForm(forms.Form):
    dossiers = forms.ModelMultipleChoiceField(
        label=_('Dossiers'),
        queryset=Dossier.objects.filter(status=Dossier.ACTIVE),
        widget=ModelSelect2MultipleWidget(
            model=Dossier, search_fields=['title__icontains'], max_results=10, attrs={'data-minimum-input-length': 0}
        ),
        help_text=_('Select one or more dossiers to be associated.')
    )


class DossierTagForm(forms.Form):
    """Base form to add or remove m2m from a dossier"""
    dossiers = forms.ModelMultipleChoiceField(
        queryset=Dossier.objects.none(), required=False, widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Dossiers which the user is a curator of
        user_dossiers = Dossier.objects.dossiers_from_user(self.user)

        self.fields['dossiers'].queryset = user_dossiers


class DossierOrganisationForm(DossierTagForm):
    """Form to add or remove organisations from a dossier"""

    def __init__(self, *args, organisation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organisation = organisation
        # Pre-selects the dossiers which the organisation is already a partner of
        self.initial['dossiers'] = self.fields['dossiers'].queryset.filter(organisations=organisation)


class DossierUserForm(DossierTagForm):
    """Form to add or remove users from a dossier"""

    def __init__(self, *args, collaborator=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-selects the dossiers which the user is already a collaborator
        self.initial['dossiers'] = self.fields['dossiers'].queryset.filter(users=collaborator)
