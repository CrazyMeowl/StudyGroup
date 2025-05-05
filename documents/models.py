from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

import os
# from .models import Document
from .utils import ingest_document_chunks

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        raise ValidationError('Only PDF, DOCX, and TXT files are allowed.')

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/',validators=[validate_file_extension])
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reports = models.JSONField(default=list)  # Store reported reasons here
    def __str__(self):
        return self.title


@receiver(post_save, sender=Document)
def on_document_approved(sender, instance, created, **kwargs):
    # only ingest when status just turned to 'approved'
    if not created and instance.status == 'approved':
        # you might want to run this in a background task (Celery/RQ) if files are large
        ingest_document_chunks(instance)
