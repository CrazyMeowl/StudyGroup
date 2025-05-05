from django.shortcuts import render, redirect
from .models import Document
from .forms import DocumentUploadForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
import os
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .forms import ReportDocumentForm

ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt']


def upload_document(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = DocumentUploadForm(request.POST, request.FILES)
        uploaded_file = request.FILES['file']
        ext = os.path.splitext(uploaded_file.name)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            messages.error(request, "File extension not supported.")
            return redirect('upload_document')

        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, "Document uploaded successfully!")
            return redirect('upload_document')
    else:
        form = DocumentUploadForm()

    return render(request, 'documents/upload_document.html', {'form': form})

def document_list(request):
    documents = Document.objects.filter(status='approved')
    form = ReportDocumentForm() 
    return render(request, 'documents/document_list.html', {'documents': documents,'form': form})
    # documents = Document.objects.all()
    # return render(request, 'documents/document_list.html', {'documents': documents})


# documents/views.py
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def moderate_documents(request):
    documents = Document.objects.filter(status='pending')
    return render(request, 'documents/moderate_documents.html', {'documents': documents})

@staff_member_required
def moderate_document_action(request, document_id):
    if request.method == 'POST':
        document = get_object_or_404(Document, id=document_id)
        action = request.POST.get('action')
        if action == 'approve':
            document.status = 'approved'
        elif action == 'reject':
            document.status = 'rejected'
        document.save()
    return redirect('moderate_documents')

# documents/views.py

@staff_member_required
def approved_documents(request):
    documents = Document.objects.filter(status='approved')
    return render(request, 'documents/approved_documents.html', {'documents': documents})

# documents/views.py

@staff_member_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if request.method == 'POST':
        document.file.delete()  # delete the file from storage
        document.delete()       # delete the model record
    return redirect('approved_documents')

@login_required
def report_document(request, document_id):
    doc = get_object_or_404(Document, id=document_id, status='approved')
    if request.method == 'POST':
        form = ReportDocumentForm(request.POST)
        if form.is_valid():
            entry = {
                'reason': form.cleaned_data['reason'],
                'comment': form.cleaned_data['comment'],
                'reported_by': request.user.username,
            }
            # Assuming you have a JSONField `reports` on Document:
            reports = doc.reports or []
            reports.append(entry)
            doc.reports = reports
            doc.save()
            messages.success(request, "Thank you — your report has been submitted.")
            return redirect('document_list')
    else:
        form = ReportDocumentForm()

    return render(request, 'documents/report_document.html', {
        'document': doc,
        'form': form,
    })

@staff_member_required
def reported_documents(request):
    """
    Show all documents that have at least one report.
    """
    # Fetch documents where the JSONField 'reports' list is non‑empty
    reported_docs = Document.objects.exclude(reports=[])  
    return render(request, 'documents/reported_documents.html', {
        'documents': reported_docs
    })
