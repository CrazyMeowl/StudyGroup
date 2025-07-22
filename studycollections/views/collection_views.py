from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.utils.html import strip_tags
from django.db.models import Q
from django.contrib import messages
from ..forms import (
    CollectionForm,
    DocumentUploadForm,
    FlashcardForm,
    MultipleChoiceQuestionForm,
)
from django.views.decorators.http import require_http_methods

from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Collection
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse
import threading
from ..models import CollaborationInvite
from django.urls import reverse

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import os

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404

import json
import random
from .utils import *
from ..chat_utils import delete_studycollection_from_chromadb
from django.views.decorators.http import require_POST

@login_required
def collection_list(request):
    user = request.user

    owned_collections = Collection.objects.filter(created_by=user)

    editor_collections = Collection.objects.filter(
        collaborators=user
    ).exclude(created_by=user)

    viewer_collections = Collection.objects.filter(
        viewers=user
    ).exclude(created_by=user).exclude(id__in=editor_collections.values_list('id', flat=True))

    return render(request, 'studycollections/collection_list.html', {
        'owned_collections': owned_collections,
        'shared_collections': editor_collections,
        'viewer_collections': viewer_collections,
    })

@login_required
def create_collection(request):
    """Create a new collection."""
    if request.method == 'POST':
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.created_by = request.user
            collection.save()
            form.save_m2m()
            return redirect('collection_list')
    else:
        form = CollectionForm()
    return render(request, 'studycollections/create_collection.html', {
        'form': form,
    })

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.user != collection.created_by:
        messages.error(request, "You don't have permission to delete this collection.")
        return redirect('collection_detail', collection_id=collection.id)

    if request.method == "POST":
        # Delete from ChromaDB
        try:
            delete_studycollection_from_chromadb(collection_id)
        except Exception as e:
            print(f"[DEBUG] Failed to delete from ChromaDB: {e}")
        collection.delete()
        messages.success(request, "Collection deleted successfully.")
        return redirect('collection_list') 

    return redirect('collection_detail', collection_id=collection.id)

def browse_public_collections(request):
    """Browse and optionally search/filter public collections."""
    q = request.GET.get('q', '')
    creator = request.GET.get('creator', '')

    collections = Collection.objects.filter(privacy='public').order_by('-created_at')
    if q:
        collections = collections.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
    if creator:
        collections = collections.filter(created_by__username__icontains=creator)

    return render(request, 'studycollections/public_collections.html', {
        'collections': collections,
        'query': q,
        'creator': creator,
    })


@login_required
@require_POST
def toggle_collection_privacy(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.user != collection.created_by:
        messages.error(request, "You do not have permission to change this collection's privacy.")
        return redirect('collection_detail', collection_id=collection.id)

    
    if collection.privacy == 'private':
        collection.privacy = 'public' 
    else:
        collection.privacy = 'private'
    collection.save()
    messages.success(request, f"Collection is now {'public' if collection.privacy == 'public' else 'private'}.")
    return redirect('collection_detail', collection_id=collection.id)


# @login_required
# def collection_detail(request, collection_id):
#     collection = get_object_or_404(Collection, id=collection_id)

#     if not user_can_view(request.user, collection):
#         return HttpResponseForbidden("You do not have permission to view this collection.")

#     context = {
#         'collection'  : collection,
#         'is_editor'   : user_can_edit(request.user, collection),
#         'flashcards'  : collection.flashcards.all(),
#         'mcqs'        : collection.mcqs.all(),
#         'multipart_questions': collection.multipart_questions.all(),
#     }
#     return render(request, 'studycollections/collection_detail.html', context)

@login_required
def study_mode(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if not user_can_view(request.user, collection):
        return HttpResponseForbidden()

    flashcards = list(collection.flashcards.all())
    mcqs = list(collection.mcqs.all())
    multipart = list(collection.multipart_questions.all())

    # Optionally shuffle or filter
    random.shuffle(flashcards)
    random.shuffle(mcqs)
    random.shuffle(multipart)

    return render(request, 'studycollections/study_mode.html', {
        'collection': collection,
        'flashcards': flashcards,
        'mcqs': mcqs,
        'multipart_questions': multipart,
    })


@login_required
def manage_collaborators(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if not user_can_edit(request.user, collection):
        messages.error(request, "You don't have permission to manage collaborators.")
        return redirect('collection_detail', collection.id)

    if request.method == 'POST':
        action = request.POST.get('action')
        identifier = request.POST.get('identifier', '').strip()
        user_id = request.POST.get('user_id')

        if action in ['invite', 'add_viewer'] and identifier:
            # Try to find user by username or email
            user = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()
            if not user:
                messages.error(request, "No user found with that username or email.")
            elif user == request.user:
                messages.warning(request, "You can't add yourself.")
            elif action == 'invite':
                if user in collection.collaborators.all():
                    messages.info(request, "User is already a collaborator.")
                elif CollaborationInvite.objects.filter(collection=collection, invitee=user, accepted=False).exists():
                    messages.info(request, "User has already been invited.")
                else:
                    invite = CollaborationInvite.objects.create(
                        collection=collection,
                        invitee=user,
                        inviter=request.user
                    )
                    threading.Thread(target=send_invitation_email, args=(request, invite)).start()
                    messages.success(request, f"Invitation sent to {user.username}.")
            elif action == 'add_viewer':
                if user in collection.viewers.all():
                    messages.info(request, "User is already a viewer.")
                else:
                    collection.viewers.add(user)
                    messages.success(request, f"Added {user.username} as a viewer.")

        elif action == 'remove_collaborator' and user_id:
            user = get_object_or_404(User, id=user_id)
            collection.collaborators.remove(user)

            # Clean up any existing invite (accepted or not)
            CollaborationInvite.objects.filter(collection=collection, invitee=user).delete()

            messages.success(request, f"Removed {user.username} as collaborator.")

        elif action == 'cancel_invite' and user_id:
            invite = CollaborationInvite.objects.filter(collection=collection, invitee__id=user_id, accepted=False).first()
            if invite:
                invite.delete()
                messages.success(request, "Invitation canceled.")

        elif action == 'remove_viewer' and user_id:
            user = get_object_or_404(User, id=user_id)
            collection.viewers.remove(user)
            messages.success(request, f"Removed {user.username} as viewer.")

        return redirect('manage_collaborators', collection_id=collection.id)

    return render(request, 'studycollections/manage_collaborators.html', {
        'collection': collection,
        'collaborators': collection.collaborators.all(),
        'viewers': collection.viewers.all(),
        'invites': CollaborationInvite.objects.filter(collection=collection, accepted=False),
    })

# def send_invitation_email(request, invite):
#     subject = f"You've been invited to collaborate on '{invite.collection.title}'"
#     url = request.build_absolute_uri(reverse('accept_invite', args=[invite.id]))
#     message = f"Hello {invite.invitee.username},\n\nYou have been invited to collaborate on the collection '{invite.collection.title}'.\nClick here to accept: {url}"

#     try:
#         send_mail(subject, message, settings.EMAIL_HOST_USER, [invite.invitee.email])
#     except BadHeaderError:
#         print("Invalid header found when sending mail.")
#     except Exception as e:
#         print(f"Error sending mail: {e}")

class EmailThread(threading.Thread):
    """
    A thread to send emails in the background, preventing UI lag.
    Supports sending both plain text and HTML emails.
    """
    def __init__(self, subject, message, from_email, recipient_list, html_message=None, fail_silently=False):
        """
        Initializes the EmailThread.

        Args:
            subject (str): The subject line of the email.
            message (str): The plain text body of the email (used as fallback for HTML).
            from_email (str): The sender's email address.
            recipient_list (list): A list of recipient email addresses.
            html_message (str, optional): The HTML body of the email. Defaults to None.
            fail_silently (bool, optional): If True, exceptions during sending are suppressed. Defaults to False.
        """
        self.subject = subject
        self.message = message
        self.from_email = from_email
        self.recipient_list = recipient_list
        self.html_message = html_message
        self.fail_silently = fail_silently
        super().__init__() # Correct way to call parent constructor in Python 3

    def run(self):
        """
        Executes the email sending logic in the new thread.
        Uses EmailMultiAlternatives if html_message is provided, otherwise falls back to send_mail.
        """
        try:
            if self.html_message:

                msg = EmailMultiAlternatives(
                    self.subject,
                    self.message, # Plain text version
                    self.from_email,
                    self.recipient_list
                )
                msg.attach_alternative(self.html_message, "text/html")
                msg.send(fail_silently=self.fail_silently)
            else:
                send_mail(
                    subject=self.subject,
                    message=self.message,
                    from_email=self.from_email,
                    recipient_list=self.recipient_list,
                    fail_silently=self.fail_silently,
                )
            print(f"Email sent successfully to: {self.recipient_list}") 
        except Exception as e:
            print(f"Error sending email to {self.recipient_list}: {e}")
            if not self.fail_silently:
                raise

def send_invitation_email(request, invite):
    subject = f"You've been invited to collaborate on '{invite.collection.title}'"
    accept_url = request.build_absolute_uri(reverse('accept_invite', args=[invite.id]))

    context = {
        'invite': invite,
        'accept_url': accept_url,
        'site_name': get_current_site(request).name,
        'from_email': settings.EMAIL_HOST_USER,
    }

    html_message = render_to_string('email/invitation_email.html', context)
    plain_message = strip_tags(html_message)

    from_email = settings.EMAIL_HOST_USER
    to_email = [invite.invitee.email]

    # Send the email in a separate thread
    EmailThread(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=to_email,
        html_message=html_message
    ).start()

@login_required
def accept_invite(request, invite_id):
    invite = get_object_or_404(CollaborationInvite, id=invite_id, invitee=request.user)
    if invite.accepted:
        messages.info(request, "You’ve already accepted this invitation.")
    else:
        invite.collection.collaborators.add(request.user)
        invite.accepted = True
        invite.save()
        messages.success(request, f"You are now a collaborator on '{invite.collection.title}'.")

    return redirect('collection_detail', invite.collection.id)


@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if not user_can_view(request.user, collection):
        return HttpResponseForbidden("You do not have permission to view this collection.")

    context = {
        'collection'  : collection,
        'is_editor'   : user_can_edit(request.user, collection),
        'flashcards'  : collection.flashcards.all(),
        'mcqs'        : collection.mcqs.all(),
        'multipart_questions': collection.multipart_questions.all(),
        'document_form': DocumentUploadForm(),
        'documents': collection.documents.all(),
    }
    return render(request, 'studycollections/collection_detail.html', context)


@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    # Only allow owner or collaborators to edit
    if not user_can_edit(request.user, collection):
        messages.error(request, "You don't have permission to edit this collection.")
        return redirect("collection_detail", collection_id=collection_id)

    if request.method == "POST":
        form = CollectionForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, "Collection updated successfully.")
            return redirect("collection_detail", collection_id=collection_id)
    else:
        form = CollectionForm(instance=collection)

    return render(request, "studycollections/edit_collection.html", {"form": form, "collection": collection})
