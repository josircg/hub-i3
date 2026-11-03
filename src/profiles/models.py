import uuid

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from organisations.models import Organisation
from utilities.clean import validate_orcid


class InterestArea(models.Model):
    interestArea = models.TextField()

    def __str__(self):
        return f'{self.interestArea}'

    class Meta:
        verbose_name = _('Interest Area')
        verbose_name_plural = _('Interest Areas')


class BaseProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
    slug = models.UUIDField(
        default=uuid.uuid4,
        blank=True,
        editable=False)
    # Add more user profile fields here. Make sure they are nullable
    # or with default values
    picture = models.ImageField(
        _("Profile picture"),
        upload_to="profile_pics/%Y-%m-%d/",
        null=True,
        blank=True
    )
    title = models.CharField(_("Title"), max_length=200, blank=True, null=True)
    bio = models.TextField(
        _("Short Bio and disciplinary background"),
        max_length=2000,
        blank=True,
        null=True)
    interestAreas = models.ManyToManyField(InterestArea, blank=True)
    orcid = models.CharField(
        "ORCID",
        help_text=_("If you have registered on the ORCID platform for researchers, "
                    "you may add your persistent digital identifier, or ORCID iD, to link "
                    "this profile with your professional information such as affiliations, "
                    "grants, publications, peer review, and more."),
        max_length=50,
        blank=True,
        null=True)

    language = models.CharField(max_length=5, choices=settings.TRANSLATED_LANGUAGES,
                                verbose_name=_('Language'), default=settings.LANGUAGE_CODE)
    lattes_id = models.CharField(
        _("Lattes ID"),
        help_text=_("If you have registered on the Lattes platform, "
                    "you may add your Lattes iD, to link this profile with your professional information "
                    "such as affiliations, grants and publications."),
        max_length=16, blank=True, null=True)

    organisation = models.ManyToManyField(Organisation, blank=True)
    email_verified = models.BooleanField(_("Email verified"), default=False)
    country = CountryField(
        blank_label=_('country'),
        null=True,
        blank=True)

    # Privacy and subscriptions
    profileVisible = models.BooleanField(verbose_name=_('Profile visible'), default=False)
    contentVisible = models.BooleanField(default=True)
    digest = models.BooleanField(default=True)

    # Permission to manage projects from a country
    manageProjectsFromCountry = CountryField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.orcid and not validate_orcid(self.orcid):
            raise ValidationError(_('Invalid ORCID'))
        super().save(*args, **kwargs)

    @property
    def has_professional_info(self):
        return bool(self.lattes_id) or bool(self.orcid)


class Profile(BaseProfile):
    def __str__(self):
        return _("{}'s profile").format(self.user)
