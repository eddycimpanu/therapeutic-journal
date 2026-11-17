from django.urls import path

from . import views

app_name = "journal"

urlpatterns = [
    path("azi/", views.today_entry, name="today"),
]