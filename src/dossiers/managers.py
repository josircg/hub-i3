from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import QuerySet, Count, Q, Value, IntegerField, Prefetch
from django.utils.translation import get_language


class DossierObjectQuerySet(QuerySet):

    def posts(self):
        post_cls = django_apps.get_model('blog', 'Post')
        post_type = ContentType.objects.get_for_model(post_cls)
        return self.filter(content_type=post_type)

    def approved_items(self):
        return self.filter(approved=True)

    def first_dossier(self):
        """Returns the first approved dossier in the queryset"""
        obj = self.approved_items().filter(dossier__status='A').first()
        return obj.dossier if obj else None


class DossierCuratorQuerySet(QuerySet):

    def annotate_dossierobject(self):
        """Returns a queryset with not moderated items count and total items."""
        return self.annotate(
            pending_count=Count('dossier__dossierobject', filter=Q(dossier__dossierobject__approved=None),
                                distinct=True),
            total_count=Count('dossier__dossierobject'),
        )


class DossierQuerySet(QuerySet):

    def dossiers_from_user(self, user):
        """Returns a queryset of dossiers from a given user"""
        return self.filter(dossiercurator__curator=user).distinct()

    def dossiers_from_object(self, **kwargs):
        """
        Returns a queryset of dossiers from a given object in kwargs.
        The object_id must be dossierobject__related_query_name__pk=object.pk.
        Example: dossiers_from_object(dossierobject__project__pk=project_id)
        """
        return self.filter(dossierobject__approved=True, **kwargs)

    def approved_dossiers(self):
        return self.filter(status='A')

    def get_approved_dossier(self, *args, **kwargs):
        """Attempts to retrieve a single approved dossier matching the given lookup parameters."""
        try:
            obj = self.approved_dossiers().get(*args, **kwargs)
            return obj
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

    def annotate_dossierobject(self, user):
        """Returns a queryset with not moderated items count and total items."""
        if user.is_authenticated:
            return self.annotate(
                total_items=Count('dossierobject'),
                pending_items=Count(
                    'dossierobject',
                    filter=Q(dossierobject__approved__isnull=True)
                ),
                user_is_curator=Count(
                    'dossiercurator',
                    filter=Q(dossiercurator__curator=user)
                )
            )
        else:
            return self.annotate(user_is_curator=Value(0, output_field=IntegerField()))

    def with_translations(self):
        """Returns a queryset of dossiertranslation whose translations match the current language"""
        language = get_language()
        dossiertranslation_cls = django_apps.get_model('dossiers', 'DossierTranslation')

        return self.prefetch_related(
            Prefetch(
                'dossiertranslation_set',
                queryset=dossiertranslation_cls.objects.filter(language=language),
                to_attr='current_translation'
            )
        )
