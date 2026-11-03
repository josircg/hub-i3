from ckeditor.widgets import CKEditorWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from django_select2 import forms as s2forms
from django_select2.forms import ModelSelect2Widget
from projects.models import Project

from . import models

User = get_user_model()


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(Field("name"))
        self.helper.layout = Layout(Field("email"))
        self.fields['name'].label = _('First Name and Surname')

    class Meta:
        model = User
        fields = ["name", "email"]


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("title"),
            Field("country"),
            Field("picture"),
            Field("bio"),
            Field("orcid"),
            Field("interestAreas"),
            Field("language"),
            Field("latitude"),
            Field("longitude"),
            Submit("update", "Update", css_class="btn-green"),
        )
        self.fields["lattes_id"].help_text = models.Profile._meta.get_field("lattes_id").help_text

    bio = forms.CharField(
        widget=CKEditorWidget(config_name='frontpage'),
        max_length=2000,
        required=False)
    interestAreas = forms.ModelMultipleChoiceField(
        queryset=models.InterestArea.objects.all(),
        widget=s2forms.ModelSelect2TagWidget(
            search_fields=['interestArea__icontains'],
            blank_label=_('None'),
            attrs={
                'data-token-separators': '[","]'}),
        required=False,
        label=_('Interest Areas'),
        help_text=_("Please write or select 2 to 3 interest areas, separated by commas or by "
                    "pressing enter"))
    lattes_id = forms.CharField(
        max_length=200,
        required=False
    )
    country = CountryField(blank=True).formfield()
    language = forms.ChoiceField(
        label=_('Language'),
        help_text=_('Select your preferred language to browse and receive emails from Cívis upon logging in.'),
        choices=settings.TRANSLATED_LANGUAGES)
    country.label = _('Country')

    class Meta:
        model = models.Profile
        fields = ["picture", "title", "bio", "orcid", "lattes_id", "language", "interestAreas"]

    def clean_orcid(self):
        data = self.cleaned_data["orcid"]
        if data:
            data = data.split('/')[-1]
        return data

    def clean_lattes_id(self):
        data = self.cleaned_data["lattes_id"]
        if data:
            data = data.split('/')[-1]
        return data

    def save(self, args):
        p_form = super(ProfileForm, self).save(commit=False)
        p_form.user = args.user
        p_form.interestAreas.set(self.data.getlist('interestAreas'))
        p_form.country = self.data['country']
        p_form.save()
        return 'success'


class UserProjectForm(forms.Form):
    """Form that lists user's projects"""
    project = forms.ModelChoiceField(
        label=_('Project'),
        queryset=Project.objects.none(),
        widget=ModelSelect2Widget(
            model=Project, search_fields=['name__icontains'], max_results=10, attrs={'data-minimum-input-length': 0}
        ),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = Project.objects.by_user_with_stats(user)
