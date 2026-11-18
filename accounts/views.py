from django.contrib.auth import login
from django.shortcuts import redirect, render
from .decorators import patient_required, therapist_required

from .forms import RegistrationForm

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User

from django.utils import timezone

def home(request):
    return render(request, "accounts/home.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})
    
    
@patient_required
def patient_dashboard(request):
    patient = request.user.patient
    hour = timezone.localtime().hour
    if 5 <= hour < 12:
        greeting = "Bună dimineața"
    elif 12 <= hour < 18:
        greeting = "Bună ziua"
    else:
        greeting = "Bună seara"

    return render(
        request,
        "accounts/patient_dashboard.html",
        {
            "patient": patient,
            "greeting": greeting,
            "wrote_today": patient.entries.filter(date=timezone.localdate()).exists(),
        },
    )


@therapist_required
def therapist_dashboard(request):
    return render(
        request,
        "accounts/therapist_dashboard.html",
        {"patients": request.user.patients.all()},
    )
    
@login_required
def dashboard(request):
    user = request.user
    if user.role == User.Role.THERAPIST:
        return redirect("accounts:therapist_dashboard")
    if hasattr(user, "patient"):
        return redirect("accounts:patient_dashboard")
    if user.is_staff:
        return redirect("admin:index")
    raise PermissionDenied