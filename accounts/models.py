from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "Pacient"
        THERAPIST = "therapist", "Terapeut"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.PATIENT
    )


class Patient(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient"
    )
    therapist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients",
        limit_choices_to={"role": User.Role.THERAPIST},
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    consent_version = models.CharField(max_length=20, default="v1")

    class Meta:
        verbose_name = "pacient"
        verbose_name_plural = "pacienți"
        ordering = ["id"]

    def __str__(self):
        return self.code

    @property
    def code(self):
        return f"P{self.pk:02d}"