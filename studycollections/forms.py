# studycollections/forms.py

from django import forms
from .models import Collection

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'privacy']  # Add any fields you want to include
