
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
from ..chat_utils import ingest_flashcard_to_chromadb, delete_flashcard_from_chromadb

@login_required
def add_flashcard(request, collection_id):
    """Add a flashcard to the collection (editors only)."""
    collection = get_object_or_404(Collection, id=collection_id)
    if not user_can_edit(request.user, collection):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = FlashcardForm(request.POST)
        if form.is_valid():
            flashcard = form.save(collection=collection, created_by=request.user)
            ingest_flashcard_to_chromadb(flashcard)
            messages.success(request, "Flashcard Added Successfully!")
            return redirect('collection_detail', collection_id)
        else:
            messages.warning(request, "Failed Adding Flashcard!")
    else:
        form = FlashcardForm()

    return render(request, 'studycollections/add_flashcard.html', {
        'form': form,
        'collection': collection,
    })

@login_required
def edit_flashcard(request, collection_id, pk):
    collection = get_object_or_404(Collection, id=collection_id)
    flashcard = get_object_or_404(Flashcard, id=pk, collection=collection)

    if not user_can_edit(request.user, collection):
        return redirect('collection_detail', collection.id)

    if request.method == 'POST':
        form = FlashcardForm(request.POST, instance=flashcard)
        if form.is_valid():
            flashcard = form.save()
            ingest_flashcard_to_chromadb(flashcard)
            messages.success(request, "Flashcard Updated Successfully!")
            return redirect('collection_detail', collection_id=collection.id)
        else:
            messages.warning(request, "Failed Updating Flashcard!")
    else:
        form = FlashcardForm(instance=flashcard)

    return render(request, 'studycollections/edit_flashcard.html', {
        'form': form,
        'collection': collection,
        'flashcard': flashcard,
    })

@login_required
@require_http_methods(["POST"])
def delete_flashcard(request, collection_id, pk):
    flashcard = get_object_or_404(Flashcard, pk=pk)
    collection = get_object_or_404(Collection, id=collection_id)
    if not user_can_edit(request.user, collection):
        return HttpResponseForbidden()
    try:
        delete_flashcard_from_chromadb(flashcard)
        flashcard.delete()
        messages.success(request, "Flashcard Deleted Successfully!")
        return redirect('collection_detail', collection_id)
    except Exception as e:
        messages.warning(request, "Failed Deleting Flashcard!")
        return redirect('collection_detail', collection_id)
