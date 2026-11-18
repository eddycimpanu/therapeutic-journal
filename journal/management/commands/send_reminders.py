from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import Patient


class Command(BaseCommand):
    help = "Trimite reminderul de seară pacienților care n-au scris azi."

    def handle(self, *args, **options):
        today = timezone.localdate()
        patients = (
            Patient.objects.filter(reminders_enabled=True, user__is_active=True)
            .exclude(entries__date=today)
            .exclude(last_reminder_sent=today)
            .exclude(user__email="")
            .select_related("user")
        )

        link = settings.SITE_URL + reverse("journal:today")
        body = render_to_string("journal/emails/reminder.txt", {"link": link})

        sent = 0
        for patient in patients:
            send_mail(
                subject="Câteva rânduri despre ziua de azi?",
                message=body,
                from_email=None,
                recipient_list=[patient.user.email],
            )
            patient.last_reminder_sent = today
            patient.save(update_fields=["last_reminder_sent"])
            sent += 1

        self.stdout.write(self.style.SUCCESS(f"Remindere trimise: {sent}"))