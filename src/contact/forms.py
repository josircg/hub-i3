import time

from captcha.fields import CaptchaField
from django import forms
from django.utils.translation import ugettext_lazy as _


class ContactForm(forms.Form):
    from_email = forms.EmailField(
        label=_('From email'),
        required=True
    )
    name = forms.CharField(label=_('Name'), required=True)
    surname = forms.CharField(label=_('Surname'), required=False)
    subject = forms.CharField(label=_('Subject'), required=True)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), required=True)
    newsletter = forms.BooleanField(label=_('I want to receive the newsletter from Cívis'), required=False)
    captcha = CaptchaField()
    # Hidden field for Time Check
    form_timestamp = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self.fields['form_timestamp'].initial = str(int(time.time()))

    def clean(self):
        cleaned_data = super().clean()

        # Time Check — blocks submissions in less than 5 seconds
        ts = cleaned_data.get('form_timestamp')
        if ts:
            try:
                elapsed = int(time.time()) - int(ts)
                if elapsed < 5:
                    raise forms.ValidationError(_('Form submitted too fast. Please try again.'))
            except (ValueError, TypeError):
                raise forms.ValidationError(_('Invalid form data.'))

        return cleaned_data


class SubmitterContactForm(forms.Form):
    subject = forms.CharField(label=_('Subject'), required=True)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), required=True)


class SubscribeForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)
    organisation = forms.CharField(label=_('Organisation'), required=False)


class ImportForm(forms.Form):
    file = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'accept': '.csv'}), required=True)
    source = forms.CharField(label=_('Origin'), required=True, help_text=_('Describe the file origin'))