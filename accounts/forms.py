from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import CURRENT_CONSENT_VERSION, Patient, User

from django.contrib.auth.forms import AuthenticationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    consent = forms.BooleanField(
        required=True,
        label="Am citit informațiile despre studiu și sunt de acord să particip.",
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Există deja un cont cu acest email.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.role = User.Role.PATIENT
        user.save()
        Patient.objects.create(user=user, consent_version=CURRENT_CONSENT_VERSION)
        return user
    


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def clean_username(self):
        return self.cleaned_data["username"].lower()