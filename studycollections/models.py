# studycollections/models.py
from django.db import models
from django.contrib.auth.models import User

class Collection(models.Model):
    PRIVACY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    shared_with = models.ManyToManyField(User, related_name='shared_collections', blank=True)
    collaborators = models.ManyToManyField(User, related_name='collaborative_collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title  # fixed here
