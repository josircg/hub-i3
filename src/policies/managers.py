from django.db import models


class PolicyQuerySet(models.QuerySet):
    """Queryset with the filters used to list public policies."""

    def approved(self):
        """Return the policies that are approved and not hidden."""
        return self.filter(approved=True, visible=True)
