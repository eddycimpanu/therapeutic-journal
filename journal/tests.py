from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Patient, User

from .models import Emotion, JournalEntry


def make_patient(username="p@example.com"):
    user = User.objects.create_user(username=username, password="test-pass")
    return Patient.objects.create(user=user)


def make_entry(patient, **overrides):
    data = {
        "patient": patient,
        "date": date(2026, 11, 13),
        "text": "O zi obișnuită.",
        "mood": 6,
        "emotions": [Emotion.JOY],
    }
    data.update(overrides)
    return JournalEntry.objects.create(**data)


class JournalEntryModelTests(TestCase):
    def test_only_one_entry_per_day(self):
        patient = make_patient()
        make_entry(patient)

        with self.assertRaises(IntegrityError), transaction.atomic():
            make_entry(patient)

    def test_two_patients_can_write_on_the_same_day(self):
        make_entry(make_patient("a@example.com"))
        make_entry(make_patient("b@example.com"))
        self.assertEqual(JournalEntry.objects.count(), 2)

    def test_mood_outside_1_10_is_rejected_by_database(self):
        patient = make_patient()
        for bad_mood in (0, 11):
            with self.assertRaises(IntegrityError), transaction.atomic():
                make_entry(patient, mood=bad_mood)

    def test_entries_are_deleted_with_patient(self):
        patient = make_patient()
        make_entry(patient)

        patient.delete()
        self.assertEqual(JournalEntry.objects.count(), 0)

    def test_text_is_optional(self):
        entry = make_entry(make_patient(), text="")
        self.assertEqual(entry.text, "")