from django import forms
from django.conf import settings
from django.db.models import BLANK_CHOICE_DASH
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from .models import Event, EventMode


class EventForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': _('Title of the event')}), label=_('Title'))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': _('A brief description of the event')}),
                                  max_length=3000, label=_('Description'))
    place = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'placeholder': _('Location of the Event')}),
                            required=False, label=_('Place'))
    mode = forms.ModelChoiceField(
        queryset=EventMode.objects.none(),
        label=_('Type'),
        widget=forms.Select(attrs={'class': 'js-example-basic-single'}),
        help_text=_('Please indicate if the event is on-line, physical or hybrid.')
    )
    language = forms.ChoiceField(
        label=_('Language'), help_text=_('Indicate the language of the event.'),
        choices=BLANK_CHOICE_DASH + settings.LANGUAGES
    )
    start_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label=_('Start date'))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label=_('End date'))
    hour = forms.TimeField(widget=forms.TextInput(attrs={'type': 'time'}), required=False, label=_('Hour'))
    url = forms.URLField(help_text=_('Copy and paste the full event URL.'), max_length=200, label=_('URL'),
                         widget=forms.TextInput(
                             attrs={'placeholder': _('Please provide a URL to the event website. '
                                                     'Include http:// or https://')}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mode'].queryset = EventMode.objects.translated_sorted_by_text()

    def save(self, args):
        pk = self.data.get('eventID', '')
        hour = self.data['hour']
        if hour == '':
            hour = None
        if pk:
            event = get_object_or_404(Event, id=pk)
            event.title = self.data['title']
            event.description = self.data['description']
            event.place = self.data['place']
            event.start_date = self.data['start_date']
            event.end_date = self.data['end_date']
            event.hour = hour
            event.url = self.cleaned_data['url']
            event.creator = args.user
            event.mode = self.cleaned_data['mode']
            event.language = self.cleaned_data['language']
        else:
            event = Event(title=self.data['title'], description=self.data['description'], place=self.data['place'],
                          start_date=self.data['start_date'], end_date=self.data['end_date'], hour=hour,
                          url=self.cleaned_data['url'], creator=args.user, mode=self.cleaned_data['mode'],
                          language=self.cleaned_data['language']
                          )
        event.save()

        return event.pk

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _('The end date cannot be earlier than the start date'))

        return cleaned_data
