from django_select2.forms import ModelSelect2TagWidget

from .models import Keyword


class KeywordsSelect2TagWidget(ModelSelect2TagWidget):
    model = Keyword
    search_fields = ['keyword__icontains']

    def value_from_datadict(self, data, files, name):
        """Create Keyword objects for given non-pimary-key values. Returns a set of all primary keys."""
        values = set(super().value_from_datadict(data, files, name))
        ivalues = set(filter(lambda i: i.isdecimal(), values))
        ivalues.update({self.get_queryset().create(keyword=val).pk for val in values - ivalues})
        return ivalues

    def build_attrs(self, base_attrs, extra_attrs=None):
        default_attrs = {
            "data-token-separators": '[","]',
        }
        default_attrs.update(base_attrs)
        return super().build_attrs(default_attrs, extra_attrs)
