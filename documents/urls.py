from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('', views.document_list, name='document_list'),
    path('moderate/', views.moderate_documents, name='moderate_documents'),
    path('moderate/<int:document_id>/', views.moderate_document_action, name='moderate_document_action'),
    path('approved/', views.approved_documents, name='approved_documents'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('<int:document_id>/report/', views.report_document, name='report_document'),
    path('reported/', views.reported_documents, name='reported_documents'),
]
