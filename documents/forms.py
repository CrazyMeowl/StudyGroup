from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'description']

# documents/forms.py
from django import forms

class ReportDocumentForm(forms.Form):
    REASONS = [
        ('duplication', 'Duplication'),
        ('inappropriate', 'Inappropriate Content'),
        ('irrelevant', 'Irrelevant'),
        ('other', 'Other'),
    ]
    reason = forms.ChoiceField(choices=REASONS, label="Reason")
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows':3}), 
        required=False, 
        label="Additional details (optional)"
    )
