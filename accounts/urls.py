from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailLoginForm

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("inregistrare/", views.register, name="register"),
    path(
        "autentificare/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=EmailLoginForm,
        ),
        name="login",
    ),
    path("deconectare/", auth_views.LogoutView.as_view(), name="logout"),
]