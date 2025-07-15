
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib import messages
from ..forms import (
    CollectionForm,
    FlashcardForm,
    MultipleChoiceQuestionForm,
)
from django.views.decorators.http import require_http_methods

from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Collection, Flashcard, MultipartQuestion, MultipartMCQ, MultipleChoiceQuestion
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse
import threading
from ..models import CollaborationInvite
from django.urls import reverse

from django.shortcuts import render, redirect
from ..models import Document
# from .forms import DocumentUploadForm
# from .forms import ReportDocumentForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
import os

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

import json
import random
from .utils import *
from ..chat_utils import ingest_multipart_question_to_chromadb, delete_multipart_question_from_chromadb

@login_required
@require_http_methods(["GET", "POST"])
def add_multipart_question(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.method == "POST":
        instructions = request.POST.get('instructions', '').strip()
        parts_json = request.POST.get('mcq_parts_json')

        if not instructions or not parts_json:
            messages.error(request, "Please provide both instructions and at least one MCQ part.")
            return render(request, 'studycollection/add_multipart.html', {'collection': collection})

        try:
            parts = json.loads(parts_json)
        except json.JSONDecodeError:
            messages.error(request, "There was an error processing your question parts.")
            return render(request, 'studycollection/add_multipart.html', {'collection': collection})

        if not parts:
            messages.error(request, "You must add at least one MCQ part.")
            return render(request, 'studycollection/add_multipart.html', {'collection': collection})

        # Create the multipart question
        multipart_question = MultipartQuestion.objects.create(
            collection=collection,
            instructions=instructions,
            created_by=request.user,
            created_at=timezone.now()
        )

        # Create the parts
        for part in parts:
            MultipartMCQ.objects.create(
                multipart=multipart_question,
                question_text=part.get('question_text', ''),
                answers=part.get('answers', []),
                correct_indices=part.get('correct_indices', []),
                multiple_correct=True
            )

        ingest_multipart_question_to_chromadb(multipart_question)
        messages.success(request, "Multipart question added successfully.")
        return redirect('collection_detail', collection_id=collection.id)

    return render(request, 'studycollections/add_multipart.html', {'collection': collection})




@login_required
@require_http_methods(["GET", "POST"])
def edit_multipart(request, collection_id, pk):
    multipart = get_object_or_404(MultipartQuestion, pk=pk)
    collection = get_object_or_404(Collection, id=collection_id)

    if not user_can_edit(request.user, collection):
        return redirect('collection_detail', collection.id)

    if request.method == 'POST':
        instructions = request.POST.get('instructions', '').strip()
        parts_json = request.POST.get('mcq_parts_json', '[]')

        if not instructions or not parts_json:
            messages.error(request, "Please provide both instructions and at least one MCQ part.")
            return render(request, 'studycollections/edit_multipart.html', {
                'multipart': multipart,
                'collection': collection
            })

        try:
            parts = json.loads(parts_json)
        except json.JSONDecodeError:
            messages.error(request, "There was an error processing your question parts.")
            return render(request, 'studycollections/edit_multipart.html', {
                'multipart': multipart,
                'collection': collection
            })

        if not parts:
            messages.error(request, "You must include at least one MCQ part.")
            return render(request, 'studycollections/edit_multipart.html', {
                'multipart': multipart,
                'collection': collection
            })

        # Update instructions
        multipart.instructions = instructions
        multipart.save()

        # Delete old parts
        multipart.parts.all().delete()

        # Create new parts
        for part in parts:
            MultipartMCQ.objects.create(
                multipart=multipart,
                question_text=part.get('question_text', ''),
                answers=part.get('answers', []),
                correct_indices=part.get('correct_indices', []),
                multiple_correct=True
            )
        ingest_multipart_question_to_chromadb(multipart)
        messages.success(request, "Multipart question updated successfully.")
        return redirect('collection_detail', collection.id)

    # Prepare parts for JavaScript (convert to JSON string)
    parts = [
        {
            'question_text': p.question_text,
            'answers': p.answers,
            'correct_indices': p.correct_indices,
            'multiple_correct': p.multiple_correct
        }
        for p in multipart.parts.all()
    ]

    return render(request, 'studycollections/edit_multipart.html', {
        'multipart': multipart,
        'collection': collection,
        'parts_json': json.dumps(parts)
    })

@login_required
@require_http_methods(["POST"])
def delete_multipart(request,collection_id, pk):
    multipart = get_object_or_404(MultipartQuestion, pk=pk)
    collection = get_object_or_404(Collection, id=collection_id)
    if not user_can_edit(request.user, collection):
        return HttpResponseForbidden()
    delete_multipart_question_from_chromadb(multipart)
    multipart.delete()
    return redirect('collection_detail', multipart.collection.id)
