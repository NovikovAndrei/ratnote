from datetime import date, time
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Exercise, Puppy, PuppyTrainingExercise, PuppyTrainingSession


class PuppyDiaryLoginRedirectTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="owner",
            password="password",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="password",
        )
        self.puppy = Puppy.objects.create(
            owner=self.owner,
            pet_name="Hanzo",
            sex="M",
            birth_date=date(2026, 1, 1),
        )
        self.session = PuppyTrainingSession.objects.create(
            puppy=self.puppy,
            date=date(2026, 6, 15),
            start_time=time(10, 0),
            end_time=time(10, 30),
            notes="Старая тренировка",
        )
        exercise = Exercise.objects.create(name="Сидеть", default_reps=3)
        PuppyTrainingExercise.objects.create(
            session=self.session,
            exercise=exercise,
            planned_reps=3,
            actual_reps=2,
            pros="Хороший фокус",
            cons="Устал",
        )
        self.diary_url = reverse("puppy_diary", args=[self.puppy.id])
        self.shared_path = f"{self.diary_url}?date=2026-06-15"

    def test_anonymous_user_is_redirected_to_login_with_next(self):
        response = self.client.get(self.shared_path)
        location = urlparse(response["Location"])

        self.assertEqual(response.status_code, 302)
        self.assertEqual(location.path, reverse("login_page"))
        self.assertEqual(parse_qs(location.query), {"next": [self.shared_path]})

    def test_successful_login_redirects_back_to_shared_link(self):
        response = self.client.post(
            f"{reverse('login_page')}?next={self.shared_path}",
            {
                "username": "owner",
                "password": "password",
                "next": self.shared_path,
            },
        )

        self.assertRedirects(
            response,
            self.shared_path,
            fetch_redirect_response=False,
        )

    def test_owner_can_view_shared_link_after_login(self):
        self.client.login(username="owner", password="password")

        response = self.client.get(self.shared_path)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дневник щенка")
        self.assertContains(response, "Старая тренировка")
        self.assertContains(response, "Добавить тренировку")

    def test_other_user_cannot_view_someone_elses_puppy(self):
        self.client.login(username="other", password="password")

        response = self.client.get(self.shared_path)

        self.assertEqual(response.status_code, 404)
