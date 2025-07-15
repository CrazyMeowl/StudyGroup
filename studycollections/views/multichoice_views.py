
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
from ..chat_utils import ingest_mcq_to_chroma
@login_required
def add_multiple_choice_question(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if not user_can_edit(request.user, collection):
        return redirect('collection_detail', collection_id)

    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        answers = json.loads(request.POST.get('answers', '[]'))
        correct_indices = json.loads(request.POST.get('correct_indices', '[]'))
        print(f"Correct indices : {correct_indices}")
        if not question_text:
            messages.error(request, "Question text cannot be empty.")
        elif len(answers) < 2:
            messages.error(request, "Please provide at least two answer options.")
        elif not correct_indices:
            messages.error(request, "Please mark at least one correct answer.")
        else:
            mcq = MultipleChoiceQuestion.objects.create(
                collection=collection,
                question_text=question_text,
                multiple_correct=True,
                answers=answers,
                correct_indices=correct_indices,
                created_by=request.user
            )
            ingest_mcq_to_chroma(mcq) # add to chromadb
            return redirect('collection_detail', collection_id)

    return render(request, 'studycollections/add_mcq.html', {
        'collection': collection,
    })




@login_required
def edit_mcq(request, collection_id, pk):
    mcq = get_object_or_404(MultipleChoiceQuestion, pk=pk)
    collection = mcq.collection

    # if not user_can_edit(request.user, collection):
    #     return HttpResponseForbidden("You don't have permission to edit this flashcard.")
    if not user_can_edit(request.user, collection):
        return redirect('collection_detail', collection.id)

    if request.method == 'POST':
        mcq.question_text = request.POST.get('question_text', '')
        mcq.multiple_correct = True
        mcq.answers = json.loads(request.POST.get('answers', '[]'))
        mcq.correct_indices = json.loads(request.POST.get('correct_indices', '[]'))
        mcq.save()
        ingest_mcq_to_chroma(mcq)  # remove from chromadb, then add again
        return redirect('collection_detail', collection.id)

    return render(request, 'studycollections/edit_mcq.html', {'mcq': mcq, 'collection': mcq.collection})


@login_required
@require_http_methods(["POST"])
def delete_mcq(request, collection_id, pk):
    mcq = get_object_or_404(MultipleChoiceQuestion, pk=pk)
    collection = get_object_or_404(Collection, id=collection_id)
    if not user_can_edit(request.user, collection):
        return HttpResponseForbidden()
    mcq.delete()
    return redirect('collection_detail', mcq.collection.id)
