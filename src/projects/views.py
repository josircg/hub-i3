import copy
import csv
import json
import logging
from datetime import datetime

import pytz
from accounts.models import ActivationTask
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import DELETION
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import ProgrammingError, transaction
from django.db.models import Q, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import formats, translation
from django.utils.timezone import get_default_timezone
from django.utils.translation import ugettext as _, get_language
from dossiers.models import Dossier
from eucs_platform import send_email, visao, set_pages_and_get_object_list, get_main_page
from eucs_platform.logger import log_message
from eucs_platform.utils import get_message_list
from rest_framework import status
from utilities.file import crop_and_save
from utilities.keyword_utils import update_keywords_dict
from utilities.models import SearchIndex, SearchIndexType

from .forms import (ProjectForm, ProjectTranslationForm, ProjectGeographicLocationForm,
                    InviteProjectForm)
from .models import (Project, Topic, ParticipationTask, Status, FollowedProjects, FundingBody, ProjectPermission, Likes,
                     Stats)

User = get_user_model()
logger = logging.getLogger("django.request")


@login_required(login_url='/login')
def newProject(request):
    user = request.user
    initial = {'language': get_language()}
    form = ProjectForm(initial=initial)
    return render(request, 'project_form.html', {'form': form, 'user': user})


@login_required
def saveProjectAjax(request):
    request.POST = request.POST.copy()
    request.POST = update_keywords_dict(request.POST)
    request.POST = updateFundingBody(request.POST)
    form = ProjectForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            images = [
                crop_and_save(request, form, 'image1', '1'), crop_and_save(request, form, 'image2', '2'),
                crop_and_save(request, form, 'image3', '3', final_width=1320),
            ]
            pk = form.save(request, images, [], '')
            # We have pk after save and not projectID (this means is a new project)
            if pk and not request.POST.get('projectID').isnumeric():
                messages.success(request, _('Project added correctly!'))
                sendProjectEmail(pk, request.user)
            elif pk and request.POST.get('projectID').isnumeric():
                messages.success(request, _('Project updated correctly!'))

            if '_save_and_indicate' in request.POST:
                ctype = ContentType.objects.get_for_model(Project)
                redirect_to = reverse('dossiers:dossier_select', kwargs={'ctype_id': ctype.pk, 'object_id': pk})
            else:
                redirect_to = reverse('project', kwargs={'pk': pk})

            return JsonResponse(
                {'Created': 'OK', 'Project': pk, 'messages': get_message_list(request), 'redirect_to': redirect_to},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(str(e), extra={'request': request})
            return JsonResponse({'Created': 'NO', 'Project': 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        if 'latitude' in form.errors:
            form.errors['logo'] = form.errors['latitude']
            del form.errors['latitude']

        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


def sendProjectEmail(pk, user):
    project = get_object_or_404(Project, id=pk)
    user_email = [user.email]
    bcc_list = copy.copy(settings.EMAIL_RECIPIENT_LIST)
    try:
        send_email(
            subject=_('Your project "%s" was submitted!') % project.name,
            message=render_to_string(f'emails/{get_language()}/new_project.html', {
                'username': user.name,
                'domain': settings.DOMAIN,
                'projectname': project.name,
                'projectid': pk}),
            to=user_email,
            bcc=bcc_list,
        )

        with translation.override(settings.LANGUAGE_CODE):
            send_email(
                subject=_('Notification - New project "%s" submitted') % project.name,
                message=render_to_string(f'emails/{settings.LANGUAGE_CODE}/notify_project.html', {
                    'username': user.name,
                    'domain': settings.DOMAIN,
                    'projectname': project.name,
                    'projectid': pk}),
                reply_to=user_email,
                to=settings.EMAIL_CIVIS,
                bcc=bcc_list
            )
    except Exception as e:
        log_message(project, f'sendProjectEmail error: {e}')


def updateFundingBody(dictio):
    fundingbodies = dictio.pop('funding_body', None)
    if fundingbodies:
        for fb in fundingbodies:
            if not fb.isdecimal():
                # This is a new funding body
                FundingBody.objects.get_or_create(body=fb)
                fb_id = FundingBody.objects.get(body=fb).id
                dictio.update({'funding_body': fb_id})
            else:
                # This funding body is already in the database
                dictio.update({'funding_body': fb})
    return dictio


@login_required
def getProjectTranslation(request):
    project = get_object_or_404(Project, id=request.POST['projectId'])
    translation = project.translatedProject.filter(inLanguage=request.POST['language'])
    if not translation:
        return HttpResponse({}, status=status.HTTP_404_NOT_FOUND, content_type="application/json")
    else:
        translation_json = serializers.serialize('json', translation)
        return HttpResponse(translation_json, status=status.HTTP_200_OK, content_type="application/json")


def submitProjectTranslation(request):
    form = ProjectTranslationForm(request.POST)
    if form.is_valid():
        form.save(request)
        return JsonResponse(
            {'UpdatedTranslation': 'OK', 'Project': request.POST['projectId']}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


@login_required(login_url='/login')
def editProject(request, pk):
    project_obj = get_object_or_404(Project, id=pk)

    user = request.user

    if not has_permission_to_edit_project(project_obj, user):
        return redirect('../projects', {})

    start_datetime = None
    end_datetime = None

    if project_obj.start_date:
        start_datetime = formats.date_format(project_obj.start_date, 'Y-m-d')
    if project_obj.end_date:
        end_datetime = formats.date_format(project_obj.end_date, 'Y-m-d')

    form = ProjectForm(initial={
        'project_name': project_obj.name,
        'url': project_obj.url,
        'start_date': start_datetime,
        'latitude': project_obj.latitude,
        'longitude': project_obj.longitude,
        'keywords': project_obj.keywords.all,
        'end_date': end_datetime,
        'description': project_obj.description,
        'description_citizen_science_aspects': project_obj.description_citizen_science_aspects,
        'status': project_obj.status,
        'mainOrganisation': project_obj.mainOrganisation,
        'organisation': project_obj.organisation.all,
        'topic': project_obj.topic.all,
        'participationTask': project_obj.participationTask.all,
        'projectGeographicLocation': project_obj.projectGeographicLocation,
        'image1': project_obj.image1,
        'image_credit1': project_obj.imageCredit1,
        'withImage1': (True, False)[project_obj.image1 == ""],
        'image2': project_obj.image2,
        'image_credit2': project_obj.imageCredit2,
        'withImage2': (True, False)[project_obj.image2 == ""],
        'image3': project_obj.image3,
        'image_credit3': project_obj.imageCredit3,
        'withImage3': (True, False)[project_obj.image3 == ""],
        'how_to_participate': project_obj.howToParticipate,
        'equipment': project_obj.equipment,
        'contact_person': project_obj.author,
        'contact_person_email': project_obj.author_email,
        'host': project_obj.host,
        'funding_body': project_obj.fundingBody.all,
        'doingAtHome': project_obj.doingAtHome,
        'fundingBodySelected': project_obj.fundingBody,
        'fundingProgram': project_obj.fundingProgram,
        'originDatabase': project_obj.originDatabase,
        'originUID': project_obj.originUID,
        'originURL': project_obj.originURL,
        'geoExtend': project_obj.geoExtend_id,
        'language': project_obj.language
    })

    return render(request, 'project_form.html', {
        'form': form,
        'project': project_obj,
        'user': user
    })


@login_required
def translateProject(request, pk):
    project = get_object_or_404(Project, id=pk)
    user = request.user

    form = ProjectTranslationForm()

    return render(request, 'translation_form.html', {
        'form': form,
        'project': project,
        'user': user})


def projects(request):
    user = request.user
    projects = Project.objects.translated()
    topics = Topic.objects.translated_sorted_by_text()
    status = Status.objects.translated_sorted_by_text()
    participationTask = ParticipationTask.objects.translated_sorted_by_text()
    dossier = Dossier.objects.get_approved_dossier(pk=request.GET.get('dossier') or 0)
    countries_with_content = projects.countries_with_content()

    # I think this is not needded
    filters = {
        'keywords': '',
        'dossier': '',
        'topic': '',
        'status': 0,
        'host': '',
        'approved': '',
        'doingAtHome': '',
        'featured': ''}

    projects = applyFilters(request, projects)
    projects = projects.distinct()
    filters = setFilters(request, filters)
    projects = projects.filter(hidden=False)

    if user.is_authenticated:
        likes = Likes.objects.filter(user=user).values_list('project', flat=True)
        follows = FollowedProjects.objects.filter(user=user).values_list('project', flat=True)
    else:
        likes = None
        follows = None

    # Ordering
    if request.GET.get('orderby'):
        orderBy = request.GET.get('orderby')
        if "featured" in orderBy:
            projectsTop = projects.filter(featured=True)
            projectsTopIds = list(projectsTop.values_list('id', flat=True))
            projects = projects.exclude(id__in=projectsTopIds)
            projects = list(projectsTop) + list(projects)
        if "name" in orderBy:
            projects = projects.order_by('name')
        if 'totalAccesses' in orderBy:
            projects = projects.order_by('-totalAccesses')
        if 'totalLikes' in orderBy:
            projects = projects.order_by('-totalLikes')
    else:
        projects = projects.order_by('-dateUpdated')

    try:
        counter = len(projects)
    except ProgrammingError:
        counter = 0
        projects = Project.objects.none()

    paginator = Paginator(projects, 16)
    page = request.GET.get('page')
    projects = paginator.get_page(page)

    return render(request, 'projects.html', {
        'projects': projects,
        'topics': topics,
        'countriesWithContent': countries_with_content,
        'status': status,
        'filters': filters,
        'participationTask': participationTask,
        'counter': counter,
        'likes': likes,
        'follows': follows,
        'isSearchPage': True,
        'dossier': dossier,
    })


@transaction.atomic
def project(request, pk):
    user = request.user
    project_obj = get_object_or_404(Project.objects.translated(), id=pk)

    if project_obj.projectGeographicLocation:
        form = ProjectGeographicLocationForm(
            initial={'projectGeographicLocation': project_obj.projectGeographicLocation})
    else:
        form = None

    # Check project permission to edit
    has_permission_to_edit = has_permission_to_edit_project(project_obj, user)

    if not has_permission_to_edit and not project_obj.approved or project_obj.hidden:
        return redirect('../projects', {})

    # Check if there is a translation
    hasTranslation = project_obj.translatedProject.filter(inLanguage=request.LANGUAGE_CODE).exists()

    # Check status
    utc = pytz.UTC
    if project_obj.end_date:
        if project_obj.end_date < utc.localize(datetime.now()):
            status = _('Completed')
        else:
            status = project_obj.status
    else:
        status = project_obj.status

    if user.is_authenticated:
        followed = project_obj.followedprojects_set.filter(user_id=user.id).exists()
        liked = project_obj.likes.filter(user=user).exists()
    else:
        followed = None
        liked = None

    if not request.user.is_staff:
        # This way will not change dateUpdated
        Project.objects.filter(pk=project_obj.pk).update(
            totalAccesses=F('totalAccesses') + 1,
            firstAccess=Coalesce('firstAccess', datetime.now(get_default_timezone()))
        )
        # Create or update stats per day
        stats = project_obj.stats.get_or_create(day=datetime.now(get_default_timezone()))[0]
        stats.accesses = F('accesses') + 1
        stats.save()

        project_obj.refresh_from_db()

    ctype = ContentType.objects.get_for_model(Project)

    return render(request, 'project.html', {
        'project': project_obj,
        'hasTranslation': hasTranslation,
        'followed': followed,
        'hasPermissionToEdit': has_permission_to_edit,
        'latitude': project_obj.latitude,
        'longitude': project_obj.longitude,
        'form': form,
        'status': status,
        'isSearchPage': True,
        'project_language_code': project_obj.language.lower(),
        'liked': liked,
        'ctype_id': ctype.pk
    })


def deleteProject(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    obj = get_object_or_404(Project, id=pk)
    log_message(obj, '', request.user, DELETION)
    obj.delete()

    return redirect('projects')


def getOtherUsers(creator):
    users = list(User.objects.all().exclude(is_superuser=True).exclude(id=creator.id).values_list('name', 'email'))
    return users


def preFilteredProjects(request):
    projects = Project.objects.get_queryset().order_by('id')
    return applyFilters(request, projects)


def applyFilters(request, projects):
    if request.GET.get('keywords'):
        projects = projects.filter(
            pk__in=SearchIndex.objects.full_text_search_ids(request.GET['keywords'], SearchIndexType.PROJECT.value)
        )

    if request.GET.get('topic'):
        topic_qs = Topic.objects.translated().filter(translated_text=request.GET['topic']).values_list('pk')
        projects = projects.filter(topic__pk__in=topic_qs)

    if request.GET.get('status'):
        # Workaround to solve the filter by calculated status
        # "Completed sent on view project (def project(request, pk))"
        if request.GET.get('status') == _('Completed'):
            projects = projects.filter(end_date__lt=pytz.UTC.localize(datetime.now()))
        else:
            status_qs = Status.objects.translated().filter(translated_text=request.GET['status']).values_list('pk')
            projects = projects.filter(status__pk__in=status_qs)

    if request.GET.get('doingAtHome'):
        projects = projects.filter(doingAtHome=request.GET['doingAtHome'])

    if request.GET.get('participationTask'):
        participationtask_qs = ParticipationTask.objects.translated().filter(
            translated_text=request.GET['participationTask']
        ).values_list('pk')
        projects = projects.filter(participationTask__pk__in=participationtask_qs)

    if request.GET.get('country'):
        projects = projects.filter(
            Q(mainOrganisation__country=request.GET['country']) | Q(country=request.GET['country']) |
            Q(organisation__country=request.GET['country'])).distinct()

    if request.GET.get('dossier'):
        projects = projects.filter(dossierobjects__dossier__pk=request.GET['dossier'],
                                   dossierobjects__approved=True).distinct()
    # Approved filters: only staff may see non-approved projects on the search page
    if request.user.is_staff and request.GET.get('approved'):
        if request.GET['approved'] == 'approved':
            projects = projects.filter(approved=True)
        elif request.GET['approved'] == 'notApproved':
            projects = projects.filter(approved=False)
        elif request.GET['approved'] == 'notYetModerated':
            projects = projects.filter(approved__isnull=True)
    else:
        projects = projects.filter(approved=True)

    return projects


def setFilters(request, filters):
    if request.GET.get('keywords'):
        filters['keywords'] = request.GET['keywords']
    if request.GET.get('topic'):
        filters['topic'] = request.GET['topic']
    if request.GET.get('status'):
        filters['status'] = request.GET['status']
    if request.GET.get('doingAtHome'):
        filters['doingAtHome'] = int(request.GET['doingAtHome'])
    if request.GET.get('approved'):
        filters['approved'] = request.GET['approved']
    if request.GET.get('participationTask'):
        filters['participationTask'] = request.GET['participationTask']
    if request.GET.get('orderby'):
        filters['orderby'] = request.GET['orderby']
    if request.GET.get('country'):
        filters['country'] = request.GET['country']
    if request.GET.get('dossier'):
        filters['dossier'] = request.GET['dossier']
    return filters


def clearFilters(request):
    return redirect('projects')


@login_required(login_url='/login')
def approve_project(request, pk, status):
    if request.user.is_staff:
        obj = setProjectApproved(request.user, pk, status == 1)

        messages.success(request, obj.get_approved_display())

        return redirect('admin:projects_project_changelist')
    else:
        messages.success(request, _('Only staff can approve object'))
        return redirect('projects')


def setProjectApproved(user, project_id, approved):
    aProject = get_object_or_404(Project, id=project_id)
    aProject.approved = False if approved in ['False', 'false', '0', False] else True
    aProject.save()
    log_message(aProject, aProject.get_approved_display(), user)
    return aProject


@staff_member_required()
def setHidden(request):
    response = {}
    id = request.POST.get("project_id")
    hidden = request.POST.get("hidden")
    setProjectHidden(id, hidden)
    return JsonResponse(response, safe=False)


def setProjectHidden(id, hidden):
    project = get_object_or_404(Project, id=id)
    project.hidden = False if hidden in ['False', 'false', '0'] else True
    project.save()


@staff_member_required()
def setFeatured(request):
    response = {}
    id = request.POST.get("project_id")
    featured = request.POST.get("featured")
    setProjectFeatured(id, featured)
    return JsonResponse(response, safe=False)


@staff_member_required()
def setProjectFeatured(id, featured):
    project = get_object_or_404(Project, id=id)
    project.featured = featured
    project.featured = False if featured in ['False', 'false', '0'] else True
    project.save()


@login_required
@transaction.atomic
def setFollowedProject(request):
    # TODO: Make a generic view to handle this operation
    if request.method == 'POST':
        project_id = request.POST.get("object_id")
        project_obj = get_object_or_404(Project, pk=project_id)
        user = request.user
        follow, created = project_obj.followedprojects_set.get_or_create(user=user)
        stats = project_obj.stats.get_or_create(day=datetime.now(get_default_timezone()))[0]
        # First, we check if the user has already followed the project
        if not created:
            # If the user has followed the project, we remove the follow
            follow.delete()
            # This way will not change dateUpdated
            Project.objects.filter(pk=project_id).update(totalFollowers=F('totalFollowers') - 1)
            # We also update the stats to know how many follows we have per day
            stats.follows = F('follows') - 1
            stats.save()
        else:
            # If the user has not followed the project, we add the follow
            Project.objects.filter(pk=project_id).update(totalFollowers=F('totalFollowers') + 1)
            # We also update the stats to know how many follows we have per day
            stats.follows = F('follows') + 1
            stats.save()

            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(project_obj.creator.email)

            try:
                language = project_obj.creator.profile.language
                with translation.override(language):
                    send_email(
                        subject=_('Your project "%s" was added as a favourite!') % project_obj.name,
                        message=render_to_string(f'emails/{language}/followed_project.html', {
                            "domain": settings.DOMAIN, "name": project_obj.name, "id": project_obj.pk
                        }), to=to
                    )
            except Exception as e:
                log_message(project_obj, f'FollowProjectEmail error: {e}')

        return JsonResponse({'Followed': created, 'Project': project_obj.id}, status=status.HTTP_200_OK)


def allowUser(request):
    response = {}
    projectId = request.POST.get("project_id")
    users = request.POST.get("users")
    project = get_object_or_404(Project, id=projectId)

    if request.user != project.creator and not request.user.is_staff:
        # TODO return JsonResponse with error code
        return redirect('../projects', {})

    # Delete all
    objs = ProjectPermission.objects.all().filter(project_id=projectId)
    if (objs):
        for obj in objs:
            obj.delete()

    # Insert all
    users = users.split(',')
    for user in users:
        fUser = User.objects.filter(email=user)[:1].get()
        projectPermission = ProjectPermission(project=project, user=fUser)
        projectPermission.save()

    return JsonResponse(response, safe=False)


# Download all projects in a CSV file
def downloadProjects(request):
    csv_file = 'nome_camada;nome_ponto;coordenadas;descricao_ponto\n'
    for rec in Project.objects.approved().filter(latitude__isnull=False):
        csv_file += 'Projeto;%s;[%s,%s];"<a href=""%s"" target=""blank"">Visualize a iniciativa</a>"\n' % (
            rec.name,
            rec.latitude,
            rec.longitude,
            'https://%s/project/%s' % (settings.DOMAIN, rec.id),
        )
    response = HttpResponse(csv_file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'
    return response


def get_headers():
    return ['id', 'name', 'description', 'keywords', 'status', 'start_date', 'end_date', 'topic', 'url', 'host',
            'howToParticipate', 'doingAtHome', 'equipment',
            'fundingBody', 'fundingProgram', 'originDatabase', 'originURL', 'originUID']


def get_data(item):
    keywordsList = list(item.keywords.all().values_list('keyword', flat=True))
    topicList = list(item.topic.all().values_list('topic', flat=True))
    participationTaskList = list(item.participationTask.all().values_list('participationTask', flat=True))

    return {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'keywords': keywordsList,
        'status': item.status,
        'start_date': item.start_date,
        'end_date': item.end_date,
        'topic': topicList,
        'participationTask': participationTaskList,
        'url': item.url,
        'latitude': item.latitude,
        'longitude': item.longitude,
        'host': item.host,
        'howToParticipate': item.howToParticipate,
        'doingAtHome': item.doingAtHome,
        'equipment': item.equipment,
        'fundingBody': item.fundingBody,
        'fundingProgram': item.fundingProgram,
        'originDatabase': item.originDatabase,
        'originURL': item.originURL,
        'originUID': item.originUID,
    }


class Buffer(object):
    def write(self, value):
        return value


def iter_items(items, pseudo_buffer):
    writer = csv.DictWriter(pseudo_buffer, fieldnames=get_headers())
    yield ','.join(get_headers()) + '\r\n'

    for item in items:
        yield writer.writerow(get_data(item))


def projects_stats(request):
    return None


def test_visao(request):
    try:
        visao.authenticate()
        return HttpResponse('Ok')
    except Exception as e:
        return HttpResponse('Falha na autenticação: %s' % e)


def send_project_invite_email(project_obj, email, user):
    if user is not None:
        language = user.profile.language
        link = f'project_invitation/{project_obj.pk}'
    else:
        language = get_language()
        link = 'signup/'

    html_message = render_to_string(f'emails/{language}/invite_to_project.html', {
        'domain': settings.DOMAIN,
        'creator': project_obj.creator.name,
        'project_id': project_obj.pk,
        'project': project_obj.name,
        'link': link
    })

    with translation.override(language):
        send_email(subject=_('Invitation to edit Project %s') % project_obj.name, to=[email], message=html_message)


@login_required
def project_invite(request):
    project_obj = get_object_or_404(Project, pk=request.POST.get('project_id'))

    check_permission_to_edit_project(project_obj, request.user)

    post_data = request.POST.copy()
    post_data['current_user'] = request.user

    form = InviteProjectForm(post_data)

    if form.is_valid():
        form.save()

        send_project_invite_email(project_obj, form.cleaned_data['email'], form.cleaned_data['user'])

        messages.success(request, _('Invitation sent succesfully!'))

        if form.cleaned_data['user'] is None:
            log_message(
                project_obj, _('Invitation sent to an unregistered email (%s)') % form.cleaned_data['email'],
                request.user
            )
        else:
            log_message(project_obj, _('Invitation sent to %s') % form.cleaned_data['user'], request.user)

        return JsonResponse({'Created': 'OK', 'project_id': project_obj.pk})
    else:
        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


@login_required(login_url='/login')
def project_invitation(request, project_id):
    try:
        project_permission = get_object_or_404(
            ProjectPermission, project__pk=project_id, user=request.user, accepted=False
        )
        project_permission.accepted = True
        project_permission.save()

        project_obj = project_permission.project
    except Http404:
        # Try to catch invitation sent to not registered users
        get_object_or_404(
            ActivationTask, email=request.user.email, task_module='projects.views', task_name='project_invitation'
        )
        # Set project permission
        project_obj = get_object_or_404(Project, pk=project_id)
        project_obj.projectpermission_set.create(user=request.user, accepted=True)

    # Log invitation confirm
    log_message(project_obj, _('%s accepted invitation to edit project') % request.user, request.user)
    messages.success(request, _('Invitation to edit project accepted!'))

    return redirect('project', pk=project_obj.pk)


@login_required
def project_permission_list(request, project_id):
    """
    Returns a page with a list of all cooperators/non registered from a project and a form to invite to edit a project.
    """
    project_obj = get_object_or_404(Project, pk=project_id)
    page_num = request.GET.get('page', 1)
    paginate_by = 20

    project_permission_paginator = Paginator(ProjectPermission.objects.all_cooperators(project_obj.pk), paginate_by)
    activationtask_paginator = Paginator(
        ActivationTask.objects.filter(
            task_module='projects.views', task_name='project_invitation', task_kwargs__project_id=project_id
        ),
        paginate_by
    )

    page_list = []
    project_permissions = set_pages_and_get_object_list(project_permission_paginator, page_list, page_num)
    activationtasks = set_pages_and_get_object_list(activationtask_paginator, page_list, page_num)
    # Get page object with max pages to command paginaton rendering
    page_obj = get_main_page(page_list)

    context = {
        'project': project_obj,
        'invite_project_form': InviteProjectForm(initial={'project_id': project_obj.pk}),
        'has_permission_to_edit': has_permission_to_edit_project(project_obj, request.user),
        'project_permissions': project_permissions,
        'activationtasks': activationtasks,
        'page_obj': page_obj
    }

    return render(request, 'projects/projectpermission_list.html', context)


@login_required
def delete_project_permission(request, permission_id):
    projectpermission = get_object_or_404(ProjectPermission.objects.select_related('project'), pk=permission_id)
    project_obj = projectpermission.project

    check_permission_to_edit_project(project_obj, request.user)

    project_id = project_obj.pk

    projectpermission.delete()

    msg = _('%s removed from project') % projectpermission.user

    # Log into project admin
    log_message(project_obj, msg, request.user)

    return JsonResponse({'deleted': 'OK', 'project_id': project_id, 'msg': msg})


@login_required
def delete_non_registered_user_invitation(request, task_id):
    """Delete project invitation activation task. Filter by task_module/task_name to get the right instance."""
    activationtask = get_object_or_404(
        ActivationTask, pk=task_id, task_module='projects.views', task_name='project_invitation'
    )
    project_obj = get_object_or_404(Project, pk=activationtask.task_kwargs['project_id'])

    check_permission_to_edit_project(project_obj, request.user)

    activationtask.delete()

    msg = _('Non registered user (%s) removed from project') % activationtask.email

    # Log into project admin
    log_message(project_obj, msg, request.user)

    return JsonResponse({'deleted': 'OK', 'project_id': project_obj.pk, 'msg': msg})


def has_permission_to_edit_project(project_obj, current_user):
    """Check if user has permission to edit a project"""
    if not hasattr(current_user, 'profile'):
        return False
    else:
        cooperators = project_obj.cooperators_as_list()
        countries_with_content = Project.objects.countries_with_content(pk=project_obj.pk)

        return current_user == project_obj.creator or current_user.is_staff or current_user.pk in cooperators \
            or current_user.profile.manageProjectsFromCountry in countries_with_content


def check_permission_to_edit_project(project_obj, current_user):
    if not has_permission_to_edit_project(project_obj, current_user):
        raise PermissionDenied


@login_required
@transaction.atomic
def like_project_ajax(request):
    # TODO: Make a generic view to handle this operation
    if request.method == 'POST':
        project_obj = get_object_or_404(Project, pk=request.POST.get('object_id'))
        user = request.user
        like, created = project_obj.likes.get_or_create(user=user)
        stats = project_obj.stats.get_or_create(day=datetime.now(get_default_timezone()))[0]
        # First, we check if the user has already liked the project
        if not created:
            # If the user has liked the project, we remove the like
            like.delete()
            # This way will not change dateUpdated
            Project.objects.filter(pk=project_obj.pk).update(totalLikes=F('totalLikes') - 1)
            # We also update the stats to know how many likes we have per day
            stats.likes = F('likes') - 1
            stats.save()
        else:
            # If the user has not liked the project, we add the like
            Project.objects.filter(pk=project_obj.pk).update(totalLikes=F('totalLikes') + 1)
            # We also update the stats to know how many likes we have per day
            stats.likes = F('likes') + 1
            stats.save()

        return JsonResponse({'Liked': created, 'Project': project_obj.pk}, status=status.HTTP_200_OK)


def generate_project_stats_ajax(request):
    stats = (
        Stats.objects
        .filter(project__id=request.POST.get('project_id'))
        .order_by("-day")
        .values('project__name', 'accesses', 'follows', 'likes', 'day')
    )
    if stats is None:
        response = {'error': 'No stats found'}
    else:
        response = json.dumps(list(stats), cls=DjangoJSONEncoder)
        response = json.loads(response)
    return JsonResponse(response, safe=False)
