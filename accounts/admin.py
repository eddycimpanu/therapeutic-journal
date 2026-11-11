from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Patient, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("role",)}),)
    list_display = ("username", "role", "is_staff")
    
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("code", "therapist", "enrolled_at")
    readonly_fields = ("code", "enrolled_at")