from django.urls import path
from . import views


urlpatterns = [
    path('', views.collection_list, name='collection_list'),
    path('create/', views.create_collection, name='create_collection'),
    path('<int:collection_id>/', views.view_collection, name='view_collection'),
    path('browse/', views.browse_public_collections, name='browse_public_collections'),
]
