import re

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import DEFAULT_TAGS, WARNING
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView
from eucs_platform import send_email
from eucs_platform.logger import log_message
from organisations.models import Organisation
from utilities.models import SearchIndex, SearchIndexType

from .forms import DossierForm, DossierObjectFormSet, DossierSelectForm, DossierOrganisationForm, DossierUserForm
from .models import Dossier, get_content_type, DossierObject
from .templatetags.dossiers_tags import has_permission_to_edit


def log_dossierobject_action(dossier, dossierobject, action, user):
    """
    Logs actions performed on DossierObject instances in the admin log style.

    :param dossier: Dossier instance to which the object belongs.
    :param dossierobject: DossierObject instance affected.
    :param action: Action type: 'deleted', 'changed', or 'added'.
    :param user: User instance performing the action.
    """
    # If no specific object is passed, log the action as applying to all
    if dossierobject is None:
        dossierobject_str = 'ALL'
    else:
        dossierobject_str = str(dossierobject)

    # Build the log message dict in the same format used by Django admin
    dct = {
        action: {
            'name': str(DossierObject._meta.verbose_name),
            'object': dossierobject_str,
        }
    }

    # Only the 'approved' field can be changed by users in this context
    if action == 'changed':
        dct[action]['fields'] = ['approved']

    # Write the log message associated with the Dossier
    log_message(dossier, [dct], user)


def add_dossier_items(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)

    if 'rebuild' in request.GET:
        dossier.dossierobject_set.all().delete()
        log_dossierobject_action(dossier, None, 'deleted', request.user)

    process_dossier(request, dossier)

    return redirect('admin:dossiers_dossier_change', dossier.pk)


def process_dossier(request, dossier):
    """Validate keywords and perform process_dossier_items"""
    if not dossier.keywords.exists():
        # Sends extra_tags to display the message with the correct css in the admin
        messages.warning(
            request, _('New items can only be added if keywords are defined.'), extra_tags=DEFAULT_TAGS[WARNING]
        )
    else:
        total = process_dossier_items(request.user, dossier)
        messages.success(request, _('%d items added') % total)


def process_dossier_items(user, dossier, keywords=None):
    if keywords is None:
        keywords = dossier.keywords.values_list('keyword', flat=True)

    order = dossier.dossierobject_set.count()
    total = 0
    models = [
        ('projects.Project', SearchIndexType.PROJECT.value),
        ('resources.Resource', SearchIndexType.RESOURCE.value),
        ('resources.TrainingResource', SearchIndexType.TRAINING.value),
        ('events.Event', SearchIndexType.EVENT.value),
        ('blog.Post', SearchIndexType.BLOG.value),
    ]

    for keyword in keywords:
        # Models with search index
        for model, index_type in models:
            model_cls = django_apps.get_model(model)
            ctype = ContentType.objects.get_for_model(model_cls)
            qs = (
                model_cls.objects.filter(
                    pk__in=SearchIndex.objects.filter(is_public=True).full_text_search_ids(keyword, index_type)
                ).exclude(pk__in=dossier.dossierobject_set.filter(content_type=ctype).values_list('object_id'))
            )

            for order, obj in enumerate(qs, start=order + 1):
                dossierobject = dossier.dossierobject_set.create(content_object=obj, order=order, approved=True)
                log_dossierobject_action(dossier, dossierobject, 'added', user)

            total += qs.count()
    # Change updated_on
    dossier.save()

    return total


class DossierListView(ListView):
    model = Dossier
    paginate_by = 12

    def get_queryset(self):
        """Returns published dossiers plus not published dossiers from user as curator"""
        user = self.request.user
        # Base QuerySet with necessary annotations and relations
        qs = super().get_queryset().select_related('post').annotate_dossierobject(user).with_translations()
        # Regex pattern for DossierObject filtering
        pattern = re.compile(r'^dossierobject__\w+__pk$')
        dossierobject_params = {k: v for k, v in self.request.GET.items() if pattern.match(k)}
        # Visibility logic for non-staff users (including anonymous)
        if not user.is_staff:
            # Filter for approved dossiers
            filters = Q(status=Dossier.ACTIVE)
            # If user is logged in, also include dossiers where they are a curator
            if user.is_authenticated:
                filters |= Q(dossiercurator__curator=user)

            qs = qs.filter(filters).distinct()
        # Apply specific DossierObject filters if present in GET params
        if dossierobject_params:
            qs = qs.dossiers_from_object(**dossierobject_params)

        return qs.order_by('-updated_on')


class DossierDetailView(DetailView):
    model = Dossier
    context_object_name = 'dossier'

    def get_queryset(self):
        return (
            super().get_queryset().select_related('post', 'forum').
            annotate_dossierobject(self.request.user).with_translations()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_permission_to_edit'] = has_permission_to_edit(self.object, self.request.user)
        context['organisations'] = self.object.organisations.all()
        context['users'] = self.object.users.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if not context.get('has_permission_to_edit', False) and not self.object.is_active:
            response = redirect('dossiers:dossiers_list')
        else:
            response = super().render_to_response(context, **response_kwargs)

        return response


@transaction.atomic
@login_required
def dossier_edit(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)

    if not has_permission_to_edit(dossier, request.user):
        return redirect('dossiers:dossiers_list')

    if request.method == 'GET':
        form = DossierForm(instance=dossier)
    else:
        form = DossierForm(request.POST, request.FILES, instance=dossier)

        if form.is_valid():
            keywords = set(dossier.keywords.values_list('keyword', flat=True))

            dossier = form.save()

            new_keywords = set(form.cleaned_data['keywords'].values_list('keyword', flat=True))
            add_keywords = new_keywords - keywords
            process_dossier_items(request.user, dossier, add_keywords)

            messages.success(request, _('Dossier updated correctly!'))

            if '_continue' in request.POST:
                to = 'dossiers:dossier_edit'
            else:
                to = 'dossiers:dossier_detail'

            return redirect(to, dossier.pk)

    return render(request, 'dossiers/dossier_form.html', {'form': form, 'dossier': dossier})


@login_required
def dossier_select(request, ctype_id, object_id):
    ctype = get_object_or_404(ContentType, pk=ctype_id)
    obj = ctype.get_object_for_this_type(pk=object_id)
    calc_ctype = get_content_type(ctype, obj)

    if request.method == 'GET':
        dossier = (
            DossierObject.objects.filter(content_type__pk=ctype_id, object_id=object_id).first_dossier()
        )
        if dossier:
            messages.warning(
                request,
                _('This content has already been associated with the dossier "%s" previously.') % dossier
            )
        form = DossierSelectForm(initial={'ctype': ctype_id, 'object_id': object_id})
    else:
        form = DossierSelectForm(request.POST)

        if form.is_valid():
            # Add to dossier and send emails
            for dossier in form.cleaned_data['dossiers']:
                order = dossier.dossierobject_set.count() + 1

                dossierobject, created = dossier.dossierobject_set.get_or_create(
                    content_type=ctype, object_id=obj.pk,
                    defaults={'order': order, 'approved': None, 'creator': request.user}
                )

                if created:
                    log_dossierobject_action(dossier, dossierobject, 'added', request.user)

                    for dossier_curator in dossier.dossiercurator_set.select_related('curator').all():
                        curator = dossier_curator.curator
                        send_dossier_select_email([curator.email], curator.profile.language, dossier, obj)

                    send_dossier_select_email(settings.EMAIL_CIVIS, settings.LANGUAGE_CODE, dossier, obj)
                else:
                    messages.warning(
                        request,
                        _('This content has already been associated with the dossier "%s" previously.') % dossier
                    )

            messages.success(request, _('Content under analysis by curatorship'))

            return redirect(obj.get_absolute_url())

    return render(request, 'dossiers/dossier_select.html', {'obj': obj, 'ctype': calc_ctype, 'form': form})


def send_dossier_select_email(to, language, dossier, obj):
    """Helper function to send an email indicating association with the dossier"""
    with translation.override(language):
        try:
            moderation_url = reverse('dossiers:dossierobjects_detail', args=(dossier.pk,))
            send_email(
                subject=_('New content has been associated with the dossier %s!') % dossier,
                message=render_to_string(
                    f'emails/{language}/dossier_select.html',
                    {"object_name": str(obj), "object_url": f'{settings.DOMAIN}{obj.get_absolute_url()}',
                     "dossier_name": str(dossier), "dossier_url": f'{settings.DOMAIN}{dossier.get_absolute_url()}',
                     "moderation_url": f'{settings.DOMAIN}{moderation_url}'}
                ),
                to=to
            )
        except Exception as e:
            log_message(dossier, f'send_dossier_select_email error: {e}')


@transaction.atomic
@login_required
def dossierobjects_edit(request, dossier_pk):
    dossier = get_object_or_404(Dossier, pk=dossier_pk)

    if not has_permission_to_edit(dossier, request.user):
        return redirect('dossiers:dossiers_list')

    if request.method == 'GET':
        formset = DossierObjectFormSet(
            instance=dossier,
            queryset=dossier.dossierobject_set.all().order_by('-approved', 'content_type__app_label')
        )
    else:
        formset = DossierObjectFormSet(request.POST, instance=dossier)

        if formset.is_valid():
            changed_objects = formset.save()

            for obj in changed_objects:
                log_dossierobject_action(dossier, obj, 'changed', request.user)

            messages.success(request, _('Dossier updated correctly!'))

            return redirect('dossiers:dossier_detail', pk=dossier.pk)

    return render(request, 'dossiers/dossierobject_form.html', {'formset': formset, 'dossier': dossier})


@login_required
def dossier_organisation(request, organisation_id):
    """Adds or removes an organisation from user dossiers"""
    organisation = get_object_or_404(Organisation.objects.filter(approved=True), id=organisation_id)

    if request.method == 'POST':
        form = DossierOrganisationForm(request.POST, user=request.user, organisation=organisation)

        if form.is_valid():
            # Selected dossiers (which will have the organisation as a partner)
            selected_dossiers = form.cleaned_data['dossiers']
            # For each dossier, add or remove the organisation as a partner
            for dossier in form.fields['dossiers'].queryset:
                if dossier in selected_dossiers:
                    dossier.organisations.add(organisation)
                else:
                    dossier.organisations.remove(organisation)

            messages.success(request, _('Partner updated successfully'))

            return redirect('organisation', pk=organisation_id)
    else:
        form = DossierOrganisationForm(user=request.user, organisation=organisation)

    return render(
        request, 'dossiers/dossier_tag.html',
        {'form': form, 'obj': organisation, 'return_url': organisation.get_absolute_url()}
    )


@login_required
def dossier_user(request, user_id):
    """Adds or removes a user from user dossiers"""
    user = get_object_or_404(
        get_user_model().objects.select_related('profile').filter(profile__profileVisible=True), id=user_id
    )

    if request.user == user:
        raise PermissionDenied(_('You cannot add yourself to your own dossiers'))

    if request.method == 'POST':
        form = DossierUserForm(request.POST, user=request.user, collaborator=user)

        if form.is_valid():
            # Selected dossiers (which will have the user as other collaborator)
            selected_dossiers = form.cleaned_data['dossiers']
            # For each dossier, add or remove the user
            for dossier in form.fields['dossiers'].queryset:
                if dossier in selected_dossiers:
                    dossier.users.add(user)
                else:
                    dossier.users.remove(user)

            messages.success(request, _('Collaborator updated successfully'))

            return redirect('profiles:show', user.profile.slug)
    else:
        form = DossierUserForm(user=request.user, collaborator=user)

    return render(
        request, 'dossiers/dossier_tag.html',
        {'form': form, 'obj': user.name, 'return_url': reverse('profiles:show', args=(user.profile.slug,))}
    )
