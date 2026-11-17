from django.contrib import admin

from .models import JournalEntry


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("patient", "date", "mood", "emotions")
    list_filter = ("date",)
    readonly_fields = ("created_at", "updated_at")