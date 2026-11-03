def add_search_index(sender, instance, created, **kwargs):
    from utilities.models import add_searchindex_text, SearchIndexType

    if instance.published:
        add_searchindex_text(SearchIndexType.BLOG.value, instance.pk, instance.title, instance.content)
    else:
        delete_search_index(None, instance)


def delete_search_index(sender, instance, **kwargs):
    from utilities.models import delete_searchindex, SearchIndexType
    delete_searchindex(SearchIndexType.BLOG.value, instance.pk)
