from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import PublicDocument
from ..forms import PublicDocumentUploadForm
from ..chat_utils import ingest_public_document_chunks
def is_moderator(user):
    return user.is_staff or user.is_superuser

# @login_required
# def upload_public_document(request):
#     if request.method == 'POST':
#         form = PublicDocumentUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             document = form.save(commit=False)
#             document.uploaded_by = request.user
#             document.save()
#             messages.success(request, "Document uploaded successfully. Awaiting moderator approval.")
#             return redirect('public_library')
#     else:
#         form = PublicDocumentUploadForm()
#     return render(request, 'library/upload_public_document.html', {'form': form})

@login_required
def upload_public_document(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = PublicDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.is_approved = False  # Pending manual approval
            try:
                document.full_clean()
                document.save()
                messages.success(request, "Document uploaded successfully and sent for review.")
                return redirect('public_library')
            except ValidationError as e:
                messages.error(request, f"Validation error: {e}")
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = PublicDocumentUploadForm()

    return render(request, 'library/upload_public_document.html', {
        'form': form
    })

@login_required
def public_library(request):
    query = request.GET.get('q', '')
    creator = request.GET.get('creator', '')

    documents = PublicDocument.objects.filter(is_approved=True)
    if query:
        documents = documents.filter(title__icontains=query)
    if creator:
        documents = documents.filter(uploaded_by__username__icontains=creator)

    return render(request, 'library/public_library.html', {
        'documents': documents,
        'query': query,
        'creator': creator,
    })