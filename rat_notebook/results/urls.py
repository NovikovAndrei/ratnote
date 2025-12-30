from django.urls import path

from .views import (
    event_list, event_detail, edit_result, delete_result, event_create, event_edit,
    login_view, custom_logout, dashboard,

    # puppies
    puppy_list, puppy_create, puppy_edit, puppy_diary,
    puppy_session_edit, puppy_session_delete,

    # legacy
    hattorihanzo_redirect,

    # existing diary helpers
    hattorihanzo_exercise_delete, hattorihanzo_exercises_reorder,

    # exercises base
    exercise_list, exercise_create, exercise_default_reps,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("dashboard/", dashboard, name="dashboard"),

    path("events/", event_list, name="event_list"),
    path("events/add/", event_create, name="event_create"),
    path("events/<int:event_id>/", event_detail, name="event_detail"),
    path("events/<int:event_id>/edit/", event_edit, name="event_edit"),
    path("results/<int:result_id>/edit/", edit_result, name="edit_result"),
    path("results/<int:result_id>/delete/", delete_result, name="delete_result"),

    path("logout/", custom_logout, name="logout"),

    # --- Puppies ---
    path("puppies/", puppy_list, name="puppy_list"),
    path("puppies/add/", puppy_create, name="puppy_create"),
    path("puppies/<int:puppy_id>/edit/", puppy_edit, name="puppy_edit"),
    path("puppies/<int:puppy_id>/diary/", puppy_diary, name="puppy_diary"),
    path("puppies/<int:puppy_id>/session/<int:pk>/edit/", puppy_session_edit, name="puppy_session_edit"),
    path("puppies/<int:puppy_id>/session/<int:pk>/delete/", puppy_session_delete, name="puppy_session_delete"),

    # --- Legacy diary URL (старое) ---
    path("hattorihanzo/", hattorihanzo_redirect, name="hattorihanzo"),

    # --- endpoints used by diary templates ---
    path("hattorihanzo/exercises/<int:pk>/delete/", hattorihanzo_exercise_delete, name="hattorihanzo_exercise_delete"),
    path("hattorihanzo/session/<int:pk>/reorder/", hattorihanzo_exercises_reorder, name="hattorihanzo_exercises_reorder"),
    path("hattorihanzo/exercises/<int:pk>/default-reps/", exercise_default_reps, name="exercise_default_reps"),

    # --- Exercises base ---
    path("exercises/", exercise_list, name="exercise_list"),
    path("exercises/add/", exercise_create, name="exercise_create"),
]
