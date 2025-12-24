from django.urls import path
from django.contrib.auth import views as auth_views
from .views import event_list, event_detail, edit_result, delete_result, event_create, event_edit, login_view, \
    custom_logout, hattorihanzo, hattorihanzo_session_edit, hattorihanzo_session_delete, hattorihanzo_exercise_delete, \
    hattorihanzo_exercises_reorder

urlpatterns = [
    # Сделаем авторизацию стартовой страницей
    path('', login_view, name='login'),  # Главная страница — форма логина

    # Список всех событий
    path('events/', event_list, name='event_list'),

    # Детали конкретного события: формы и рейтинг
    path('event/<int:event_id>/', event_detail, name='event_detail'),

    # Создание и редактирование событий
    path('add/', event_create, name='event_create'),
    path('event/<int:event_id>/edit/', event_edit, name='event_edit'),

    # Редактирование и удаление результатов внутри контекста события
    path('event/<int:event_id>/result/<int:pk>/edit/', edit_result, name='edit_result'),
    path('event/<int:event_id>/result/<int:pk>/delete/', delete_result, name='delete_result'),

    # Роут для логина
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='logout'), # Логин отдельно (чтобы можно было вручную попасть на страницу)
    # Роут для дневника щенка
    path("hattorihanzo", hattorihanzo, name="hattorihanzo"),
    path("hattorihanzo/session/<int:pk>/edit", hattorihanzo_session_edit, name="hattorihanzo_session_edit"),
    path("hattorihanzo/session/<int:pk>/delete", hattorihanzo_session_delete, name="hattorihanzo_session_delete"),
    path("hattorihanzo/exercises/<int:pk>/delete/", hattorihanzo_exercise_delete, name="hattorihanzo_exercise_delete"),
    path("hattorihanzo/session/<int:pk>/reorder", hattorihanzo_exercises_reorder, name="hattorihanzo_exercises_reorder",
),

]
