import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import formats, translation
from django.utils.translation import ugettext_lazy as _, pgettext, get_language
from dossiers.models import Dossier
from eucs_platform import send_email, set_pages_and_get_object_list
from eucs_platform.logger import log_message
from utilities.models import SearchIndex, SearchIndexType

from .forms import EventForm
from .models import Event, EventMode


def events(request):
    events
    user = request.user
    page = request.GET.get('page', 1)
    # period key = A means list all events (upcoming, ongoing, past)
    filters = {'keywords': '', 'period': 'A', 'event_mode': '', 'language': '', 'dossier': ''}
    search_filters = {}
    temporal_options = [
        ('O', pgettext('plural', 'Ongoing')),
        ('U', pgettext('plural', 'Upcoming')),
        ('P', pgettext('plural', 'Past')),
    ]

    dossier = Dossier.objects.get_approved_dossier(pk=request.GET.get('dossier') or 0)

    if request.GET.get('pk'):
        search_filters['pk'] = request.GET.get('pk')
    else:
        if request.GET.get('keywords'):
            search_filters['pk__in'] = SearchIndex.objects.full_text_search_ids(request.GET['keywords'],
                                                                                SearchIndexType.EVENT.value)
            filters['keywords'] = request.GET['keywords']

        if request.GET.get('event_mode'):
            event_mode_qs = (
                EventMode.objects.translated().filter(translated_text=request.GET['event_mode']).values_list('pk')
            )
            search_filters['mode__pk__in'] = event_mode_qs
            filters['event_mode'] = request.GET['event_mode']

        if request.GET.get('language'):
            search_filters['language'] = request.GET['language']
            filters['language'] = request.GET['language']

        if request.GET.get('period'):
            filters['period'] = request.GET['period']

        if request.GET.get('dossier'):
            search_filters['dossierobjects__dossier__pk'] = request.GET['dossier']
            search_filters['dossierobjects__approved'] = True
            filters['dossier'] = request.GET['dossier']

    event_modes = EventMode.objects.translated_sorted_by_text()
    qs = Event.objects.filter(**search_filters)
    # List upcoming if user filter by upcoming or all events
    upcoming_events = qs.upcoming_events() if filters['period'] in 'AU' else qs.none()
    # List ongoing if user filter by ongoing or all events
    ongoing_events = qs.ongoing_events() if filters['period'] in 'AO' else qs.none()
    # List past if user filter by past or all events
    past_events = qs.past_events() if filters['period'] in 'AP' else qs.none()

    if not user.is_staff:
        upcoming_events = upcoming_events.approved_events()
        ongoing_events = ongoing_events.approved_events()
        past_events = past_events.approved_events()

    try:
        counter = len(upcoming_events) + len(ongoing_events) + len(past_events)
    except ProgrammingError:
        counter = 0
        upcoming_events = Event.objects.none()
        ongoing_events = upcoming_events
        past_events = upcoming_events

    paginator_upcoming = Paginator(upcoming_events, 10)
    paginator_ongoing = Paginator(ongoing_events, 10)
    paginator_past = Paginator(past_events, 10)

    page_list = []

    upcoming_events = set_pages_and_get_object_list(paginator_upcoming, page_list, page)
    ongoing_events = set_pages_and_get_object_list(paginator_ongoing, page_list, page)
    past_events = set_pages_and_get_object_list(paginator_past, page_list, page)
    # Return the page object from paginator with max pages, to command pagination
    if page_list:
        if request.GET.get('pk'):
            # Returns page_obj with one item to build meta tags for this item
            page_obj = max(page_list, key=lambda item: item.paginator.count)
        else:
            page_obj = max(page_list, key=lambda item: item.paginator.num_pages)
    else:
        page_obj = None

    ctype = ContentType.objects.get_for_model(Event)

    return render(
        request, 'events.html', {
            'upcoming_events': upcoming_events,
            'ongoing_events': ongoing_events,
            'past_events': past_events,
            'page_obj': page_obj,
            'user': user,
            'filters': filters,
            'isSearchPage': True,
            'counter': counter,
            'event_modes': event_modes,
            'temporal_options': temporal_options,
            'ctype_id': ctype.pk,
            'dossier': dossier,
        }
    )


def sendEventEmail(event_id, request, form):
    event = get_object_or_404(Event, pk=event_id)
    to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
    to.append(request.user.email)
    messages.success(request, _('Event added correctly'))
    context = {
        'domain': settings.DOMAIN, 'submissionName': form.cleaned_data['title'],
        'username': request.user.name, 'eventid': event_id
    }

    try:
        send_email(
            subject=_('Your event "%s" was submitted!') % form.cleaned_data['title'],
            message=render_to_string(f'emails/{get_language()}/new_event.html', context), to=to,
            reply_to=settings.EMAIL_CIVIS
        )

        with translation.override(settings.LANGUAGE_CODE):
            send_email(
                subject=_('Notification - New event "%s" submitted') % form.cleaned_data['title'],
                message=render_to_string(f'emails/{settings.LANGUAGE_CODE}/notify_event.html', context),
                reply_to=to, to=settings.EMAIL_CIVIS
            )
    except Exception as e:
        log_message(event, f'sendEventEmail error: {e}')


@login_required(login_url='/login')
def new_event(request):
    user = request.user
    form = EventForm()
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            pk = form.save(request)
            sendEventEmail(pk, request, form)

            if '_save_and_indicate' in request.POST:
                ctype = ContentType.objects.get_for_model(Event)
                redirect_to = reverse('dossiers:dossier_select', kwargs={'ctype_id': ctype.pk, 'object_id': pk})
            else:
                redirect_to = 'events'

            return redirect(redirect_to)
        else:
            messages.error(request, _('Please correct the errors below.'))
    return render(request, 'event_form.html', {'form': form, 'user': user})


@login_required(login_url='/login')
def approve_event(request, pk, status):
    event = get_object_or_404(Event, id=pk)
    if request.user.is_staff:
        event.approved = status == 1
        event.save()
        if event.approved:
            message = _('Event approved')
        else:
            message = _('Event not approved')
        log_message(event, message, request.user)
        messages.success(request, message)
        return redirect('/admin/events/event/')
    else:
        messages.success(request, _('Only staff can approve object'))
        return redirect('../events', {})


@login_required(login_url='/login')
def editEvent(request, pk):
    user = request.user
    event = get_object_or_404(Event, id=pk)

    if user != event.creator and not user.is_staff:
        return redirect('events')

    start_datetime = None
    end_datetime = None
    if event.start_date:
        start_datetime = formats.date_format(event.start_date, 'Y-m-d')
    if event.end_date:
        end_datetime = formats.date_format(event.end_date, 'Y-m-d')
    form = EventForm(initial={
        'title': event.title,
        'description': event.description,
        'place': event.place,
        'start_date': start_datetime,
        'end_date': end_datetime,
        'hour': event.hour,
        'url': event.url,
        'mode': event.mode_id,
        'language': event.language,
    })
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save(request)

            if '_save_and_indicate' in request.POST:
                ctype = ContentType.objects.get_for_model(Event)
                redirect_to = reverse('dossiers:dossier_select', kwargs={'ctype_id': ctype.pk, 'object_id': pk})
            else:
                redirect_to = 'events'

            return redirect(redirect_to)
        else:
            messages.error(request, _('Please correct the errors below.'))
    return render(request, 'event_form.html', {'form': form, 'user': user, 'event': event})


def deleteEvent(request, pk):
    obj = get_object_or_404(Event, id=pk)
    if request.user == obj.creator or request.user.is_staff:
        obj.delete()
    return redirect('events')


@staff_member_required()
def setFeaturedEvent(request):
    response = {}
    id = request.POST.get("event_id")
    featured = request.POST.get("featured")
    event = get_object_or_404(Event, id=id)
    event.featured = False if featured == 'false' else True
    event.save()
    return JsonResponse(response, safe=False)
