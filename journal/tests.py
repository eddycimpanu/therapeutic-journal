from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Patient, User

from .models import Emotion, JournalEntry

from django.urls import reverse
from django.utils import timezone

from .forms import JournalEntryForm

from io import StringIO

from django.core import mail
from django.core.management import call_command

import csv
import json
import tempfile
from pathlib import Path

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
        
class HistoryViewTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.url = reverse("journal:history")

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_shows_only_own_entries(self):
        make_entry(self.patient, text="Textul meu.")
        make_entry(make_patient("altul@example.com"), text="Textul altcuiva.")

        self.client.force_login(self.patient.user)
        response = self.client.get(self.url)

        self.assertContains(response, "Textul meu.")
        self.assertNotContains(response, "Textul altcuiva.")

    def test_newest_entries_first(self):
        make_entry(self.patient, date=date(2026, 11, 10))
        make_entry(self.patient, date=date(2026, 11, 12))

        self.client.force_login(self.patient.user)
        response = self.client.get(self.url)

        dates = [entry.date for entry in response.context["entries"]]
        self.assertEqual(dates, [date(2026, 11, 12), date(2026, 11, 10)])

    def test_emotions_are_shown_in_romanian(self):
        make_entry(self.patient, emotions=["sadness"])

        self.client.force_login(self.patient.user)
        self.assertContains(self.client.get(self.url), "Tristețe")

    def test_html_in_text_is_escaped(self):
        make_entry(self.patient, text="<script>alert('x')</script>")

        self.client.force_login(self.patient.user)
        response = self.client.get(self.url)

        self.assertNotContains(response, "<script>alert")
        self.assertContains(response, "&lt;script&gt;")

class SendRemindersTests(TestCase):
    def setUp(self):
        self.patient = make_patient("ana@example.com")
        self.patient.user.email = "ana@example.com"
        self.patient.user.save()

    def run_command(self):
        call_command("send_reminders", stdout=StringIO())

    def test_sends_to_patient_without_entry_today(self):
        self.run_command()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@example.com"])

    def test_skips_patient_who_wrote_today(self):
        make_entry(self.patient, date=timezone.localdate())
        self.run_command()
        self.assertEqual(len(mail.outbox), 0)

    def test_skips_patient_with_reminders_disabled(self):
        self.patient.reminders_enabled = False
        self.patient.save()
        self.run_command()
        self.assertEqual(len(mail.outbox), 0)

    def test_does_not_send_twice_in_one_day(self):
        self.run_command()
        self.run_command()
        self.assertEqual(len(mail.outbox), 1)

    def test_email_has_link_but_no_journal_content(self):
        make_entry(self.patient, date=date(2026, 11, 10), text="Ceva foarte personal.")
        self.run_command()

        body = mail.outbox[0].body
        self.assertIn("/jurnal/azi/", body)
        self.assertNotIn("Ceva foarte personal.", body)
        self.assertNotIn(self.patient.code, body)
        
class ExportDataTests(TestCase):
    def setUp(self):
        self.patient = make_patient("ana@example.com")
        self.patient.user.email = "ana@example.com"
        self.patient.user.save()
        make_entry(self.patient, text="=SUM(A1:A2) o zi ciudată", emotions=["sadness", "fear"])

    def export(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        call_command("export_data", output_dir=tmp.name, stdout=StringIO())
        folder = Path(tmp.name)
        return next(folder.glob("*.json")), next(folder.glob("*.csv"))

    def test_json_has_code_and_no_email(self):
        json_path, _ = self.export()
        content = json_path.read_text(encoding="utf-8")
        rows = json.loads(content)

        self.assertEqual(rows[0]["patient_code"], self.patient.code)
        self.assertEqual(rows[0]["emotions"], ["sadness", "fear"])
        self.assertNotIn("ana@example.com", content)

    def test_csv_has_no_email_and_is_formula_safe(self):
        _, csv_path = self.export()
        content = csv_path.read_text(encoding="utf-8-sig")
        row = next(csv.DictReader(content.splitlines()))

        self.assertNotIn("ana@example.com", content)
        self.assertEqual(row["emotions"], "sadness;fear")
        self.assertTrue(row["text"].startswith("'="))