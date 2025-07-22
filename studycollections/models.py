from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from .chat_utils import ingest_document_chunks
class Collection(models.Model):
    PRIVACY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    collaborators = models.ManyToManyField(User, related_name='collaborative_collections', blank=True)
    viewers = models.ManyToManyField(User, related_name='viewable_collections', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Flashcard(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='flashcards')
    question = models.TextField()
    answer = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flashcard: {self.question[:50]}"
    

class MultipartQuestion(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='multipart_questions')
    instructions = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class MultipartMCQ(models.Model):
    multipart = models.ForeignKey(MultipartQuestion, on_delete=models.CASCADE, related_name='parts')
    question_text = models.TextField()
    answers = models.JSONField()
    correct_indices = models.JSONField()
    multiple_correct = models.BooleanField(default=False)

    
class MultipleChoiceQuestion(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='mcqs')
    question_text = models.TextField()
    multiple_correct = models.BooleanField(default=False)
    answers = models.JSONField(default=list)           # e.g., ["Option A", "Option B", ...]
    correct_indices = models.JSONField(default=list)    # e.g., [0, 2]
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text



class CollaborationInvite(models.Model):
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('invitee', 'collection') 



def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        raise ValidationError('Only PDF, DOCX, and TXT files are allowed.')

def collection_directory_path(instance, filename):
    return f'collections/{instance.collection.id}/{filename}'

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=collection_directory_path, validators=[validate_file_extension])
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    reports = models.ManyToManyField(User, blank=True, related_name='reported_documents')
    collection = models.ForeignKey('Collection', on_delete=models.CASCADE, related_name='documents')


class PublicDocument(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='public_library/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title