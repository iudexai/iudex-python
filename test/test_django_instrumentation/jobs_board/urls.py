from django.urls import path

from . import views

app_name = 'jobs_board'

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/<int:profile_id>", views.profile, name="profile"),
    path("profile/create", views.profile_create, name="profile_create"),
    path("profile/<int:profile_id>/evaluate", views.profile_evaluate, name="profile_evaluate"),
]
