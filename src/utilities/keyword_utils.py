from .models import Keyword


def update_keywords_dict(dictio):
    """Update a dict containing a list of keywords"""
    keywords = dictio.pop('keywords', None)

    if keywords:
        for k in keywords:
            if not k.isdecimal():
                # This is a new keyword
                obj = Keyword.objects.get_or_create(keyword=k.strip().lower())[0]
                dictio.update({'keywords': obj.pk})
            else:
                # This keyword is already in the database
                dictio.update({'keywords': k})

    return dictio


def keywords_list(keywords):
    """
    Returns a list of Keyword objects
    :param keywords: comma-separated list of keywords
    """
    final_keywords = []

    for k in keywords.split(","):
        if not k.isdecimal():
            obj = Keyword.objects.get_or_create(keyword=k.strip().lower())[0]
            final_keywords.append(obj.pk)

    return final_keywords
