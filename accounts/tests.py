from django.test import TestCase

from .models import Patient, User


def make_patient(username):
    user = User.objects.create_user(username=username, password="test-pass")
    return Patient.objects.create(user=user)


class PatientTests(TestCase):
    def test_code_is_built_from_id(self):
        patient = make_patient("a")
        self.assertEqual(patient.code, f"P{patient.pk:02d}")

    def test_code_is_not_reused_after_delete(self):
        make_patient("a")
        second = make_patient("b")
        old_code = second.code
        second.delete()

        third = make_patient("c")
        self.assertNotEqual(third.code, old_code)

    def test_consent_version_defaults_to_v1(self):
        self.assertEqual(make_patient("a").consent_version, "v1")