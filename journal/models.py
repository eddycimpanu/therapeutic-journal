from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from accounts.models import Patient


class Emotion(models.TextChoices):
    JOY = "joy", "Bucurie"
    SADNESS = "sadness", "Tristețe"
    FEAR = "fear", "Frică"
    ANGER = "anger", "Furie"
    TRUST = "trust", "Încredere"
    SURPRISE = "surprise", "Surpriză"


class JournalEntry(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="entries"
    )
    date = models.DateField(default=timezone.localdate)
    text = models.TextField(blank=True)
    mood = models.PositiveSmallIntegerField()
    emotions = ArrayField(
        models.CharField(max_length=20, choices=Emotion.choices), size=3
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "intrare de jurnal"
        verbose_name_plural = "intrări de jurnal"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "date"], name="one_entry_per_patient_per_day"
            ),
            models.CheckConstraint(
                condition=models.Q(mood__gte=1, mood__lte=10),
                name="mood_between_1_and_10",
            ),
        ]

    def __str__(self):
        return f"{self.patient.code} – {self.date:%d.%m.%Y}"