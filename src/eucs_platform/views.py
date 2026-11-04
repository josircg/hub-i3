from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.views.main import SEARCH_VAR
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, check_for_language
from django.views.i18n import set_language as sl, LANGUAGE_QUERY_PARAMETER
from django_countries import countries
from django_countries.templatetags.countries import get_country
from events.models import Event
from organisations.models import Organisation
from platforms.models import Platform
from profiles.models import Profile
from projects.models import Project, Topic as PTopic, Likes, FollowedProjects
from resources.models import Resource, ResourceGroup, ResourcesGrouped, BookmarkedResources
from utilities.models import SearchIndex

from . import set_language_preference


def home(request):
    # home is the only language-prefixed URL, so we need to get the current language to set the
    # session and cookie for the entire site. If the user enters the platform by another url, the language will
    # be defined via locale middleware and will use the session and cookie previously stored.
    current_language = get_language()
    # TODO: Clean this, we dont need lot of things
    user = request.user
    filters = {'keywords': ''}
    items_per_page = 4
    page = request.GET.get('page')

    # Projects
    projects = Project.objects.translated().approved().order_by('-dateCreated')
    paginatorprojects = Paginator(projects, items_per_page)
    projects = paginatorprojects.get_page(page)
    counterprojects = paginatorprojects.count

    # Resources
    resources = Resource.objects.approved_resources().order_by('-dateUpdated')
    paginatorresources = Paginator(resources, items_per_page)
    resources = paginatorresources.get_page(page)
    counterresources = paginatorresources.count

    # Training Resources
    training_resources = Resource.objects.approved_training_resources().order_by('-dateUpdated')
    paginator_training_resources = Paginator(training_resources, items_per_page)
    training_resources = paginator_training_resources.get_page(page)
    countertresources = paginator_training_resources.count

    # Organisations
    # TODO: Put -dateCreated
    organisations = Organisation.objects.filter(approved=True).order_by('id')
    if request.GET.get('keywords'):
        organisations = organisations.filter(Q(name__icontains=request.GET['keywords'])).distinct()
    paginatororganisation = Paginator(organisations, items_per_page)
    organisations = paginatororganisation.get_page(page)
    counterorganisations = paginatororganisation.count

    # Platforms
    platforms = Platform.objects.filter(active=True).order_by('-dateCreated')
    paginator_platform = Paginator(platforms, items_per_page)
    platforms = paginator_platform.get_page(page)
    counter_platforms = paginator_platform.count

    if settings.VISAO_USERNAME:
        base_endpoint = f'{settings.VISAO_URL}/visao2/viewGroupCategory/{settings.VISAO_GROUP}?'
        compare_topics_endpoint = None
        # compare_topics_endpoint = mark_safe(
        #     f'{settings.VISAO_URL}/app/#/visao?chart=1&grupCategory={settings.VISAO_GROUP}'
        # )

        visao_endpoint = mark_safe(
            f'{base_endpoint}l={settings.VISAO_LAYER}&amp&ui=f&amp&header=f&amp&hideIndicator=t'
        )
        project_topics = [
            (str(ptopic), f'{base_endpoint}{ptopic.external_url}')
            for ptopic in PTopic.objects.topics_with_external_url().translated().order_by('translated_text')
        ]
    else:
        compare_topics_endpoint = None
        visao_endpoint = None
        project_topics = []

    # Events
    ongoing_events = Event.objects.approved_events().ongoing_events()
    upcoming_events = Event.objects.approved_events().upcoming_events()
    # Join ongoing and upcoming events in one paginator
    paginator_event = \
        Paginator(ongoing_events.union(upcoming_events, all=True).order_by('-featured', 'start_date', 'end_date'),
                  items_per_page)
    events = paginator_event.get_page(page)

    # Users
    counter_users = Profile.objects.count()

    total = countertresources + counterprojects + countertresources + counterorganisations
    if user.is_authenticated:
        project_likes = Likes.objects.filter(user=user).values_list('project', flat=True)
        project_follows = FollowedProjects.objects.filter(user=user).values_list('project', flat=True)
        resource_follows = BookmarkedResources.objects.filter(user=user).values_list('resource', flat=True)
    else:
        project_likes = None
        project_follows = None
        resource_follows = None

    response = render(request, 'home.html', {
        'user': user,
        'projects': projects,
        'counterprojects': counterprojects,
        'resources': resources,
        'counterresources': counterresources,
        'filters': filters,
        'trainingResources': training_resources,
        'countertresources': countertresources,
        'organisations': organisations,
        'counterorganisations': counterorganisations,
        'platforms': platforms,
        'events': events,
        'counterPlatforms': counter_platforms,
        'counterUsers': counter_users,
        'total': total,
        'visao_endpoint': visao_endpoint,
        'compare_topics_endpoint': compare_topics_endpoint,
        'project_topics': project_topics,
        'project_likes': project_likes,
        'project_follows': project_follows,
        'resource_follows': resource_follows,
        'isSearchPage': True,
    })

    clanguage = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, '')
    # Only set language for anonymous users. Authenticated user has default language defined in his profile.
    if current_language != clanguage and not request.user.is_authenticated:
        response = set_language_preference(request, response, current_language)

    return response


def all(request):
    return home(request)


def about(request):
    return render(request, 'pages/%s/about.html' % get_language())


def terms(request):
    return render(request, 'pages/%s/terms.html' % get_language())


def privacy(request):
    return render(request, 'pages/%s/privacy.html' % get_language())


def curated(request):
    groups = ResourceGroup.objects.get_queryset().order_by('id')
    resourcesgrouped = ResourcesGrouped.objects.get_queryset().order_by('group')
    return render(request, 'curated.html', {
        'groups': groups,
        'resourcesgrouped': resourcesgrouped,
        'isSearchPage': False})


def imprint(request):
    return render(request, 'imprint.html')


def contact(request):
    return render(request, 'contact.html')


def development(request):
    return render(request, 'development.html')


def moderation(request):
    return render(request, 'moderation.html')


def criteria(request):
    return render(request, 'criteria.html')


def moderation_quality_criteria(request):
    return render(request, 'moderation_quality_criteria.html')


def translations(request):
    return render(request, 'translations.html')


def guide(request):
    if settings.USE_GUIDE:
        return HttpResponseRedirect("/static/site/files/%s/%s" % (get_language(), settings.USE_GUIDE))
    else:
        return render(request, 'guide.html')


def home_autocomplete(request, index_type=None):
    if request.GET.get('q'):
        text = request.GET['q']
        is_admin = request.user and request.user.is_staff
        # Inhibits blog until we add blog search.
        response = (
            SearchIndex.objects.exclude(type__type='blog').
            full_text_search_as_json(text, index_type, only_public=not is_admin)
        )
        return JsonResponse(list(response), safe=False)
    else:
        return HttpResponse("No cookies")


@staff_member_required(login_url='/login')
def country_list(request):
    """Page with admin style to list countries from django-countries"""
    if SEARCH_VAR in request.GET:
        text = request.GET.get(SEARCH_VAR)
        result = filter(lambda c: text.lower() in c.name.lower(), countries)
    else:
        result = countries
    # Return country name translations
    result = country_translation(result)

    return render(request, 'country_list.html', {'countries': result})


def country_translation(country_iterator):
    """Rebuild country list to return translations"""
    for country in country_iterator:
        country_object = get_country(country.code)
        yield {
            'code': country_object.code,
            'name_english': get_country_translated_name('en', country_object),
            'name_portuguese': get_country_translated_name('pt-br', country_object),
            'name_spanish': get_country_translated_name('es', country_object),
        }


def get_country_translated_name(language, country):
    with translation.override(language):
        return translation.gettext(country.countries.name(country.code))


def set_language(request):
    """Set user default language after language change"""
    response = sl(request)

    if request.method == 'POST' and request.user.is_authenticated:
        lang_code = request.POST.get(LANGUAGE_QUERY_PARAMETER)
        if lang_code and check_for_language(lang_code):
            profile = request.user.profile
            profile.language = lang_code
            profile.save()

    return response
