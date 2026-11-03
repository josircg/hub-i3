from urllib.parse import urlencode

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404
from django.views import generic

from .models import Post


class PostList(generic.ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = urlencode(query_params)
        context['site_name'] = settings.SITE_NAME
        return context

    queryset = (
        Post.objects.published().prefetch_related('authors').order_by('-sticky', '-created_on')
    )
    template_name = 'blog.html'
    paginate_by = '12'


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(Post.objects.published().prefetch_related('authors'), slug=slug)
    ctype = ContentType.objects.get_for_model(Post)
    return render(request, 'post_detail.html', {'post': post, "domain": settings.HOST, 'ctype_id': ctype.pk})
