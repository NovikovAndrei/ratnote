from django.urls import path

from .views import (
    event_list, event_detail, edit_result, delete_result, event_create, event_edit,
    login_view, custom_logout,
    hattorihanzo, hattorihanzo_session_edit, hattorihanzo_session_delete,
    hattorihanzo_exercise_delete, hattorihanzo_exercises_reorder,
    exercise_list, exercise_create, exercise_default_reps
)

urlpatterns = [
    # Главная страница — форма логина
    path("", login_view, name="login"),

    # Список всех событий
    path("events/", event_list, name="event_list"),

    # Детали конкретного события: формы и рейтинг
    path("event/<int:event_id>/", event_detail, name="event_detail"),

    # Создание и редактирование событий
    path("add/", event_create, name="event_create"),
    path("event/<int:event_id>/edit/", event_edit, name="event_edit"),

    # Редактирование и удаление результатов внутри контекста события
    path("event/<int:event_id>/result/<int:pk>/edit/", edit_result, name="edit_result"),
    path("event/<int:event_id>/result/<int:pk>/delete/", delete_result, name="delete_result"),

    # Логин/логаут
    path("login/", login_view, name="login"),
    path("logout/", custom_logout, name="logout"),

    # Дневник щенка
    path("hattorihanzo/", hattorihanzo, name="hattorihanzo"),
    path("hattorihanzo/session/<int:pk>/edit/", hattorihanzo_session_edit, name="hattorihanzo_session_edit"),
    path("hattorihanzo/session/<int:pk>/delete/", hattorihanzo_session_delete, name="hattorihanzo_session_delete"),
    path("hattorihanzo/exercises/<int:pk>/delete/", hattorihanzo_exercise_delete, name="hattorihanzo_exercise_delete"),
    path("hattorihanzo/session/<int:pk>/reorder/", hattorihanzo_exercises_reorder,
         name="hattorihanzo_exercises_reorder"),

    # База упражнений
    path("exercises/", exercise_list, name="exercise_list"),
    path("exercises/add/", exercise_create, name="exercise_create"),
    path("hattorihanzo/exercises/<int:pk>/default-reps/", exercise_default_reps, name="exercise_default_reps"),
]
