from django.test import TestCase

from .models import Patient, User

from .forms import RegistrationForm

from django.urls import reverse

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
        


def registration_data(**overrides):
    data = {
        "email": "Ana@Example.com",
        "password1": "o-parola-lunga-123",
        "password2": "o-parola-lunga-123",
        "consent": True,
    }
    data.update(overrides)
    return data


class RegistrationFormTests(TestCase):
    def test_valid_form_creates_user_and_patient(self):
        form = RegistrationForm(data=registration_data())
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()
        self.assertEqual(user.username, "ana@example.com")
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertEqual(user.patient.consent_version, "v1")

    def test_consent_is_required(self):
        form = RegistrationForm(data=registration_data(consent=False))
        self.assertFalse(form.is_valid())
        self.assertIn("consent", form.errors)

    def test_email_must_be_unique(self):
        RegistrationForm(data=registration_data()).save()
        form = RegistrationForm(data=registration_data(email="ana@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)        
        
class RegisterViewTests(TestCase):
    def test_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_registration_creates_patient_and_logs_in(self):
        response = self.client.post(reverse("accounts:register"), registration_data())

        self.assertRedirects(response, reverse("accounts:home"))
        self.assertTrue(Patient.objects.filter(user__username="ana@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)
        
class LoginLogoutTests(TestCase):
    def setUp(self):
        RegistrationForm(data=registration_data()).save()

    def test_login_with_email_in_any_case(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "ANA@example.com", "password": "o-parola-lunga-123"},
        )
        self.assertRedirects(response, reverse("accounts:home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "ana@example.com", "password": "parola-gresita"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_ends_session(self):
        self.client.login(username="ana@example.com", password="o-parola-lunga-123")
        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:home"))
        self.assertNotIn("_auth_user_id", self.client.session)