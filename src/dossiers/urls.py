from django.urls import path

from . import views

app_name = 'dossiers'
urlpatterns = [
    path('add-dossier-items/<int:pk>/', views.add_dossier_items, name='add_dossier_items'),
    path('dossiers/', views.DossierListView.as_view(), name='dossiers_list'),
    path('dossier/<int:pk>/', views.DossierDetailView.as_view(), name='dossier_detail'),
    path('dossier/<int:dossier_pk>/edit_dossierobjects/', views.dossierobjects_edit, name='dossierobjects_detail'),
    path('dossier_edit/<int:pk>/', views.dossier_edit, name='dossier_edit'),
    path('dossier_select/<int:ctype_id>/<int:object_id>/', views.dossier_select, name='dossier_select'),
    path('dossier_organisation/<int:organisation_id>/', views.dossier_organisation, name='dossier_organisation'),
    path('dossier_user/<int:user_id>/', views.dossier_user, name='dossier_user'),
]
