from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Patient, User

from .models import Emotion, JournalEntry

from django.urls import reverse
from django.utils import timezone

from .forms import JournalEntryForm


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
        

def entry_data(**overrides):
    data = {"text": "Am fost la facultate.", "mood": 7, "emotions": ["joy", "trust"]}
    data.update(overrides)
    return data


class JournalEntryFormTests(TestCase):
    def test_emotions_between_1_and_3(self):
        self.assertFalse(JournalEntryForm(data=entry_data(emotions=[])).is_valid())
        too_many = ["joy", "trust", "fear", "anger"]
        self.assertFalse(JournalEntryForm(data=entry_data(emotions=too_many)).is_valid())
        self.assertTrue(JournalEntryForm(data=entry_data()).is_valid())

    def test_mood_between_1_and_10(self):
        for bad_mood in (0, 11):
            form = JournalEntryForm(data=entry_data(mood=bad_mood))
            self.assertFalse(form.is_valid())


class TodayEntryViewTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.url = reverse("journal:today")

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_therapist_gets_403(self):
        therapist = User.objects.create_user(
            username="t@example.com", password="test-pass", role=User.Role.THERAPIST
        )
        self.client.force_login(therapist)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_creates_today_entry(self):
        self.client.force_login(self.patient.user)
        response = self.client.post(self.url, entry_data())

        self.assertRedirects(response, self.url)
        entry = JournalEntry.objects.get()
        self.assertEqual(entry.patient, self.patient)
        self.assertEqual(entry.date, timezone.localdate())

    def test_second_post_updates_the_same_entry(self):
        self.client.force_login(self.patient.user)
        self.client.post(self.url, entry_data(text="Dimineața."))
        self.client.post(self.url, entry_data(text="Dimineața. Și seara."))

        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertEqual(JournalEntry.objects.get().text, "Dimineața. Și seara.")