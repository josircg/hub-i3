from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from organisations.models import Organisation
from resources.models import Resource
from utilities.models import Concept, Schema

from .managers import PolicyQuerySet


class Policy(models.Model):
    """Public policy, classified through the concepts of its schemas."""
    name = models.TextField(_('Name'))
    description = models.TextField(_('Description'))
    url = models.URLField(blank=True, null=True)
    start_date = models.DateTimeField(_('Start date'))
    end_date = models.DateTimeField(_('End date'), null=True, blank=True)

    organisations = models.ManyToManyField(
        Organisation, blank=True, verbose_name=_('Organisations'))
    legislations = models.ManyToManyField(
        Resource, blank=True, verbose_name=_('Legislation'))

    # Statistics
    totalAccesses = models.IntegerField(default=0)
    totalLikes = models.IntegerField(default=0)
    totalFollowers = models.IntegerField(default=0)

    visible = models.BooleanField(_('Visible'), default=True)
    approved = models.BooleanField(_('Approved'), null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    dateCreated = models.DateTimeField(_('Created date'), auto_now_add=True)
    dateUpdated = models.DateTimeField(_('Updated date'), auto_now=True)

    objects = PolicyQuerySet.as_manager()

    class Meta:
        verbose_name = _('Public Policy')
        verbose_name_plural = _('Public Policies')

    def __str__(self):
        return f'{self.name}'

    def year(self):
        """Return the start year as text, or ``-`` when there is no start date."""
        if not self.start_date:
            return '-'
        return f'{self.start_date.year}'

    def missing_required_schemas(self):
        """Return the schemas marked as required for this policy that have no concept."""
        used_schemas = self.policyconcept_set.values('concept__schema')
        return Schema.objects.filter(
            policyschema__policy=self, policyschema__required=True
        ).exclude(pk__in=used_schemas)

    def save(self, *args, **kwargs):
        """Save the policy, approving it automatically when a staff user creates it."""
        if not self.pk and self.creator.is_staff:
            self.approved = True

        super().save(*args, **kwargs)


class PolicySchema(models.Model):
    """Schema that may categorize a policy, optionally required."""
    schema = models.ForeignKey(Schema, on_delete=models.RESTRICT)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)

    class Meta:
        unique_together = ('policy', 'schema')
        verbose_name = _('Policy Scheme')
        verbose_name_plural = _('Policy Schemes')

    def __str__(self):
        return f'{self.policy} - {self.schema}'


class PolicyConcept(models.Model):
    """Concept associated to a policy."""
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('policy', 'concept')
        verbose_name = _('Public Policy Class')
        verbose_name_plural = _('Public Policy Classes')

    def __str__(self):
        return f'{self.policy} - {self.concept}'

    def clean(self):
        """Validate that the concept belongs to one of the schemas of the policy.

        :raises ValidationError: if the concept schema is not associated with the policy
        """
        super().clean()
        # The admin inline validates this against the submitted schemas
        # (the schema may be added in the same request), so it skips this check.
        if getattr(self, 'skip_schema_validation', False):
            return
        if not (self.policy_id and self.concept_id):
            return

        allowed = PolicySchema.objects.filter(policy_id=self.policy_id, schema_id=self.concept.schema_id)
        if not allowed.exists():
            raise ValidationError({'concept': _('The concept schema is not associated with this policy.')})
