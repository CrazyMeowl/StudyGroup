from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from ..models import Document, Collection
from ..forms import DocumentUploadForm, ReportDocumentForm
from ..chat_utils import ingest_document_chunks, delete_document_chunks


@login_required
def upload_document(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.user != collection.created_by and request.user not in collection.collaborators.all():
        return HttpResponseBadRequest("You do not have permission to upload to this collection.")

    if request.method == 'POST' and request.FILES.get('file'):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.collection = collection
            try:
                document.full_clean()
                document.save()
                ingest_document_chunks(document)
                messages.success(request, "Document uploaded and processed successfully.")
                return redirect('collection_detail', collection_id=collection.id)
            except ValidationError as e:
                messages.error(request, f"Validation error: {e}")
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = DocumentUploadForm()

    return render(request, 'documents/upload_document.html', {
        'form': form,
        'collection': collection,
    })


@login_required
def report_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if request.method == 'POST':
        form = ReportDocumentForm(request.POST)
        if form.is_valid():
            report = {
                'reason': form.cleaned_data['reason'],
                'comment': form.cleaned_data['comment'],
                'reported_by': request.user.username,
            }
            reports = document.reports or []
            reports.append(report)
            document.reports = reports
            document.save()
            messages.success(request, "Report submitted. Thank you for your feedback.")
            return redirect('collection_detail', collection_id=document.collection.id)
    else:
        form = ReportDocumentForm()

    return render(request, 'documents/report_document.html', {
        'document': document,
        'form': form,
    })


@login_required
def delete_document(request, document_id, collection_id):
    document = get_object_or_404(Document, id=document_id)
    collection =  get_object_or_404(Collection, id=collection_id)

    if request.user != collection.created_by and request.user not in collection.collaborators.all():
        return HttpResponseBadRequest("You do not have permission to delete this document.")

    if request.method == 'POST':
        try:
            # Updated call with user and collection ID
            delete_document_chunks(user=request.user, document_id=document.id, collection_id=collection.id)
        except Exception as e:
            messages.warning(request, f"Warning: Error removing document from ChromaDB: {e}")

        document.file.delete(save=False)
        document.delete()

        messages.success(request, "Document deleted successfully.")
        return redirect('collection_detail', collection_id=collection.id)

    return render(request, 'documents/confirm_delete_document.html', {
        'document': document,
    })