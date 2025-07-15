from django.urls import path
from .views import collection_views, document_views, flashcard_views, multichoice_views, multipart_views, chat_views, public_document_views, admin_views

urlpatterns = [
    path('', collection_views.collection_list, name='collection_list'),
    path('create/', collection_views.create_collection, name='create_collection'),
    # path('<int:collection_id>/', views.view_collection, name='view_collection'),
    path('browse/', collection_views.browse_public_collections, name='browse_public_collections'),
    path('<int:collection_id>/', collection_views.collection_detail, name='collection_detail'),  # <-- new
    path('<int:collection_id>/delete/', collection_views.delete_collection, name='delete_collection'),
    path('<int:collection_id>/toggle-privacy/', collection_views.toggle_collection_privacy, name='toggle_collection_privacy'),
    path('<int:collection_id>/chat/', chat_views.collection_chat, name='collection_chat'),
    path('collections/<int:collection_id>/edit/', collection_views.edit_collection, name='edit_collection'),
    path('<int:collection_id>/study/', collection_views.study_mode, name='study_mode'),
    path('<int:collection_id>/invite/', collection_views.manage_collaborators, name='manage_collaborators'),
    path('invites/<int:invite_id>/accept/', collection_views.accept_invite, name='accept_invite'),

    path('<int:collection_id>/add-flashcard/', flashcard_views.add_flashcard, name='add_flashcard'),
    path('<int:collection_id>/flashcard/<int:pk>/edit/', flashcard_views.edit_flashcard, name='edit_flashcard'),
    path('<int:collection_id>/flashcard/<int:pk>/delete/', flashcard_views.delete_flashcard, name='delete_flashcard'),
    
    path('<int:collection_id>/add-mcq/', multichoice_views.add_multiple_choice_question, name='add_mcq'),
    path('<int:collection_id>/mcq/<int:pk>/edit/', multichoice_views.edit_mcq, name='edit_mcq'),
    path('<int:collection_id>/mcq/<int:pk>/delete/', multichoice_views.delete_mcq, name='delete_mcq'),

    path('<int:collection_id>/add-multipart/', multipart_views.add_multipart_question, name='add_multipart'),
    path('<int:collection_id>/multipart/<int:pk>/edit/', multipart_views.edit_multipart, name='edit_multipart'),
    path('<int:collection_id>/multipart/<int:pk>/delete/', multipart_views.delete_multipart, name='delete_multipart'),

    path('<int:collection_id>/documents/upload/', document_views.upload_document, name='upload_document'),
    path('<int:collection_id>/documents/<int:document_id>/report/', document_views.report_document, name='report_document'),
    path('<int:collection_id>/documents/<int:document_id>/delete/', document_views.delete_document, name='delete_document'),

    path('library/upload/', public_document_views.upload_public_document, name='upload_public_document'),
    path('library/', public_document_views.public_library, name='public_library'),
    
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/pending-documents/', admin_views.pending_documents, name='pending_documents'),
    path('admin/approved-documents/', admin_views.approved_documents, name='approved_documents'),
    path('admin/approve-document/<int:document_id>/', admin_views.approve_document, name='approve_document'),
    path('admin/deny-document/<int:document_id>/', admin_views.deny_document, name='deny_document'),
    path('admin/delete-approved-document/<int:document_id>/', admin_views.delete_approved_document, name='delete_approved_document'),
    path('admin/download-document/<int:document_id>/', admin_views.download_document, name='download_document'),
   
]
