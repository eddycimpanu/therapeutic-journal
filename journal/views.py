from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import patient_required

from .forms import JournalEntryForm
from .models import JournalEntry


@patient_required
def today_entry(request):
    patient = request.user.patient
    today = timezone.localdate()
    entry = JournalEntry.objects.filter(patient=patient, date=today).first()

    form = JournalEntryForm(request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.patient = patient
        entry.date = today
        entry.save()
        messages.success(request, "Intrarea de azi a fost salvată.")
        return redirect("journal:today")

    return render(
        request,
        "journal/today.html",
        {"form": form, "today": today, "is_update": entry is not None},
    )
    
@patient_required
def history(request):
    return render(
        request,
        "journal/history.html",
        {
            "entries": request.user.patient.entries.all(),
            "today": timezone.localdate(),
        },
    )