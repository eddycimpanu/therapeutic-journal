import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from journal.models import JournalEntry

FIELDS = ["patient_code", "date", "mood", "emotions", "text", "last_edited"]


def csv_safe(value):
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


class Command(BaseCommand):
    help = "Exportă intrările de jurnal în JSON și CSV, doar cu codurile participanților."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=str(settings.BASE_DIR / "exports"))

    def handle(self, *args, output_dir, **options):
        entries = JournalEntry.objects.select_related("patient").order_by("patient_id", "date")
        rows = [
            {
                "patient_code": entry.patient.code,
                "date": entry.date.isoformat(),
                "mood": entry.mood,
                "emotions": list(entry.emotions),
                "text": entry.text,
                "last_edited": timezone.localtime(entry.updated_at).isoformat(timespec="minutes"),
            }
            for entry in entries
        ]

        folder = Path(output_dir)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = timezone.localtime().strftime("%Y-%m-%d_%H%M")
        json_path = folder / f"journal_{stamp}.json"
        csv_path = folder / f"journal_{stamp}.csv"

        json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    **row,
                    "emotions": ";".join(row["emotions"]),
                    "text": csv_safe(row["text"]),
                })

        self.stdout.write(self.style.SUCCESS(
            f"{len(rows)} intrări exportate:\n  {json_path}\n  {csv_path}"
        ))