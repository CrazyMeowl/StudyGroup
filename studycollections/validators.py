import os
from django.core.exceptions import ValidationError

def validate_file_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        raise ValidationError('Only PDF, DOCX, and TXT files are allowed.')
