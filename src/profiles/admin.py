import csv

from accounts.email import send_new_user_email
from authtools.admin import NamedUserAdmin
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext

from .models import Profile, InterestArea

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = Profile


@admin.action(description=_('Export monthly stats file'))
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=user_sum.csv'

    writer = csv.writer(response)
    fields_header = ['month', 'total']
    writer.writerow(fields_header)

    counter = 0
    group = {}
    for obj in queryset.order_by('date_joined'):
        counter += 1
        mes = obj.date_joined.strftime('%Y-%m')
        group[mes] = counter

    for key, value in group.items():
        writer.writerow([key, value])
    return response


@admin.action(description=_('Send activation email'))
def send_activation_email(modeladmin, request, queryset):
    counter = 0

    for obj in queryset.select_related('profile').filter(is_active=False):
        send_new_user_email(obj)
        counter += 1

    modeladmin.message_user(request, ngettext(
        '%d email sent.',
        '%d emails sent.',
        counter,
    ) % counter, messages.SUCCESS)


class NewUserAdmin(NamedUserAdmin):
    inlines = [UserProfileInline]
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__profileVisible')
    list_display = (
        "email", "name", "permalink", "is_active", "profilevisible", "is_staff", "date_joined", "last_login",
    )
    actions = [export_as_csv, send_activation_email]

    # 'View on site' didn't work since the original User model needs to
    # have get_absolute_url defined. So showing on the list display
    # was a workaround.
    def permalink(self, obj):
        url = reverse("profiles:show", kwargs={"slug": obj.profile.slug})
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>', url, "\xb6")

    def profilevisible(self, obj):
        return obj.profile.profileVisible

    profilevisible.boolean = True
    profilevisible.short_description = _('Profile visible')
    profilevisible.admin_order_field = 'profile__profileVisible'


admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)
admin.site.register(InterestArea)
