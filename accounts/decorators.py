from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def patient_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "patient"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def therapist_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.THERAPIST:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper