# studycollections/forms.py

from django import forms
from .models import Collection, Flashcard, MultipleChoiceQuestion, Document, PublicDocument
from django.forms import modelformset_factory
from django import forms

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ReportDocumentForm(forms.Form):
    reason = forms.CharField(
        label="Reason for reporting",
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        max_length=1000
    )

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'privacy'] 
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter collection title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter a brief description (Optional)'}),
            'privacy': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Select privacy level'}),
        }

class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ['question', 'answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def save(self, commit=True, collection=None, created_by=None):
        """
        Save a Flashcard, setting collection and creator.
        """
        instance = super().save(commit=False)
        if collection:
            instance.collection = collection
        if created_by:
            instance.created_by = created_by
        if commit:
            instance.save()
        return instance

class MultipleChoiceQuestionForm(forms.ModelForm):
    answers = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text="Enter each answer on its own line."
    )
    correct_indices = forms.CharField(
        required=False,
        help_text="Comma-separated indexes of correct answers, e.g. 0,2"
    )

    class Meta:
        model = MultipleChoiceQuestion
        fields = ['question_text', 'multiple_correct', 'answers', 'correct_indices']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_answers(self):
        data = self.cleaned_data['answers']
        lines = [line.strip() for line in data.splitlines() if line.strip()]
        if len(lines) < 2:
            raise forms.ValidationError("Please enter at least two answers.")
        return lines

    def clean_correct_indices(self):
        data = self.cleaned_data.get('correct_indices', '')
        if not data:
            return []
        try:
            indices = [int(x.strip()) for x in data.split(',') if x.strip()]
        except ValueError:
            raise forms.ValidationError("Correct indices must be integers separated by commas.")
        return indices

    def save(self, commit=True, collection=None, created_by=None, part_of=None):
        instance = super().save(commit=False)
        instance.answers = self.cleaned_data['answers']
        instance.correct_indices = self.cleaned_data['correct_indices']
        if collection:
            instance.collection = collection
        if created_by:
            instance.created_by = created_by
        if part_of:
            instance.part_of = part_of
        if commit:
            instance.save()
        return instance

class PublicDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = PublicDocument
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }