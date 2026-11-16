from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from .constants import PostStatus
from .models import Post


def make_published(modeladmin, request, queryset):
    queryset.update(status=PostStatus.PUBLISHED)


make_published.short_description = _("Mark selected posts as published")


def make_draft(modeladmin, request, queryset):
    queryset.update(status=PostStatus.DRAFT)


make_draft.short_description = _("Mark selected posts as draft")


class CustomPostForm(forms.ModelForm):
    class Meta:
        model = Post
        widgets = {'content': CKEditorWidget(config_name='default')}
        fields = "__all__"


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'sticky', 'excerpt', 'created_on')
    list_filter = ("status",)
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    form = CustomPostForm
    actions = [make_published, make_draft]
    readonly_fields = ['status']
    autocomplete_fields = ['authors']

    def response_change(self, request, obj):
        if "_preview" in request.POST:
            form = CustomPostForm(request.POST)
            if form.data['title'] and form.data['excerpt'] and form.data['content']:
                post = get_object_or_404(Post, slug=form.data['slug'])
                objectA = post
                return render(request, "preview_post_detail.html", {'object': objectA, 'post': post})
            else:
                print(form.errors)

        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if "_preview" in request.POST:
            form = CustomPostForm(request.POST)
            if form.data['title'] and form.data['excerpt'] and form.data['content']:
                post = get_object_or_404(Post, slug=form.data['slug'])
                objectA = post
                return render(request, "preview_post_detail.html", {'object': objectA, 'post': post})
            else:
                print(form.errors)

        return super().response_add(request, obj, post_url_continue=None)

    def get_view_on_site_url(self, obj=None):
        """Add link to views.post_detail"""
        self.view_on_site = obj is not None and obj.published
        return super().get_view_on_site_url(obj)

    def save_model(self, request, obj, form, change):
        if '_save_and_publish' in request.POST:
            obj.status = PostStatus.PUBLISHED
        elif '_save_as_draft' in request.POST:
            obj.status = PostStatus.DRAFT

        super().save_model(request, obj, form, change)


admin.site.register(Post, PostAdmin)
