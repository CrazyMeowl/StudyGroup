from django.contrib import admin


from .models import Document

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'uploaded_by', 'reports']
    search_fields = ['title', 'status']

admin.site.register(Document, DocumentAdmin)
