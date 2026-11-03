from itertools import chain

from django.apps import apps as django_apps
from django.db.models import QuerySet, OuterRef, Subquery, F, Q
from django.db.models.functions import Coalesce
from django.utils.translation import get_language
from utilities.managers import TranslationBaseQuerySet


class ProjectPermissionQuerySet(QuerySet):

    def all_cooperators(self, project_id):
        return self.filter(project__pk=project_id)

    def cooperators(self, project_id=None):
        kwargs = {'accepted': True}

        if project_id is not None:
            kwargs['project__pk'] = project_id

        return self.filter(**kwargs)

    def cooperators_as_list(self, project_id):
        return self.cooperators(project_id).values_list('user', flat=True)

    def cooperators_emails(self, project_id):
        qs = self.cooperators(project_id).values_list('user__email', flat=True)
        return ', '.join(qs)

    def invite_accepted(self, project_id, user):
        return self.filter(project__pk=project_id, user=user, accepted=True).exists()

    def project_permissions_by_user(self, user):
        return self.filter(user=user).select_related('project')


class ProjectQuerySet(QuerySet):

    def countries_with_content(self, **kwargs):
        """
        Returns a set of countries from projects.
        It should be a model function, but we also need as a manager function to return a set from all projects.
        """
        main_organization_country = self.filter(**kwargs).values_list('mainOrganisation__country', flat=True).distinct()
        organization_country = self.filter(**kwargs).values_list('organisation__country', flat=True).distinct()
        project_country = self.filter(**kwargs).values_list('country', flat=True).distinct()

        return set(chain(main_organization_country, organization_country, project_country))

    def translated(self):
        language = get_language()
        # Intermediate Project.translatedProject M2M class
        projectm2m_cls = django_apps.get_model('projects', 'Project').translatedProject.through
        translation = projectm2m_cls.objects.filter(translatedproject__inLanguage=language, project=OuterRef('pk'))
        return self.annotate(
            description_translated=Coalesce(Subquery(translation.values('translatedproject__translatedDescription')),
                                            F('description')))

    def by_user(self, user):
        """Returns projects where user is creator or has accepted invite to be a cooperator"""
        return self.filter(
            Q(creator=user) | Q(projectpermission__user=user, projectpermission__accepted=True)
        ).distinct()

    def by_user_with_stats(self, user):
        """Returns projects where user is creator or has accepted invite and that have statistics"""
        return self.filter(stats__isnull=False).by_user(user)

    def approved(self):
        return self.filter(approved=True, hidden=False)


class TopicQuerySet(TranslationBaseQuerySet):
    default_field = 'topic'

    def topics_with_external_url(self):
        return self.filter(external_url__isnull=False).order_by('topic')

    def topics_with_projects(self):
        """Returns a QuerySet of topics with projects."""
        projects = self.values_list('project', flat=True)
        return self.filter(project__in=projects).translated().values_list('pk', 'translated_text').distinct()


class StatusQuerySet(TranslationBaseQuerySet):
    default_field = 'status'


class ParticipationTaskQuerySet(TranslationBaseQuerySet):
    default_field = 'participationTask'
