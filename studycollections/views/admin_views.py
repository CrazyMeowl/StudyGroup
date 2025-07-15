# views/admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import FileResponse, HttpResponseBadRequest
from ..models import PublicDocument
from ..chat_utils import ingest_public_document_chunks, delete_public_document_chunks

@staff_member_required
def admin_dashboard(request):
    pending_count = PublicDocument.objects.filter(is_approved=False).count()
    approved_count = PublicDocument.objects.filter(is_approved=True).count()
    return render(request, 'admin/dashboard.html', {
        'pending_count': pending_count,
        'approved_count': approved_count,
    })

@staff_member_required
def pending_documents(request):
    query = request.GET.get('q', '')
    creator = request.GET.get('creator', '')

    documents = PublicDocument.objects.filter(is_approved=False)
    if query:
        documents = documents.filter(title__icontains=query)
    if creator:
        documents = documents.filter(uploaded_by__username__icontains=creator)

    return render(request, 'admin/pending_documents.html', {
        'documents': documents,
        'query': query,
        'creator': creator,
    })

@staff_member_required
def approved_documents(request):
    query = request.GET.get('q', '')
    creator = request.GET.get('creator', '')

    documents = PublicDocument.objects.filter(is_approved=True)
    if query:
        documents = documents.filter(title__icontains=query)
    if creator:
        documents = documents.filter(uploaded_by__username__icontains=creator)

    return render(request, 'admin/approved_documents.html', {
        'documents': documents,
        'query': query,
        'creator': creator,
    })

@staff_member_required
def approve_document(request, document_id):
    doc = get_object_or_404(PublicDocument, id=document_id)
    doc.is_approved = True
    doc.save()
    ingest_public_document_chunks(doc)
    messages.success(request, "Document approved and published.")
    return redirect('pending_documents')

@staff_member_required
def deny_document(request, document_id):
    doc = get_object_or_404(PublicDocument, id=document_id)
    doc.delete()
    messages.success(request, "Document denied and deleted.")
    return redirect('pending_documents')

@staff_member_required
def delete_approved_document(request, document_id):
    doc = get_object_or_404(PublicDocument, id=document_id, is_approved=True)
    delete_public_document_chunks(doc)
    doc.delete()
    messages.success(request, "Document deleted and removed from search index.")
    return redirect('approved_documents')

@staff_member_required
def download_document(request, document_id):
    doc = get_object_or_404(PublicDocument, id=document_id)
    return FileResponse(doc.file.open(), as_attachment=True)
