from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .registration_forms import StudentRegistrationForm


class StudentRegistrationFormTests(TestCase):
    def test_accepts_ten_character_alphanumeric_username_and_password(self):
        form = StudentRegistrationForm(data={
            "username": "student123",
            "password1": "N7vQp4x!",
            "password2": "N7vQp4x!",
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_username_that_is_not_exactly_ten_alphanumeric_characters(self):
        for username in ("student12", "student1234", "student!23"):
            with self.subTest(username=username):
                form = StudentRegistrationForm(data={
                    "username": username,
                    "password1": "N7vQp4x!",
                    "password2": "N7vQp4x!",
                })
                self.assertFalse(form.is_valid())
                self.assertIn("username", form.errors)

    def test_requires_password_of_at_least_eight_characters(self):
        form = StudentRegistrationForm(data={
            "username": "student123",
            "password1": "N7vQx!",
            "password2": "N7vQx!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_requires_a_special_character_in_password(self):
        form = StudentRegistrationForm(data={
            "username": "student123",
            "password1": "N7vQp4xa",
            "password2": "N7vQp4xa",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_registration_page_renders_without_an_illustration(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="right-panel"')
        self.assertContains(response, 'class="btn-register"')
        self.assertContains(response, "10 letters or numbers")
        self.assertNotContains(response, "illustration-wrap")
        self.assertNotContains(response, "login-photo.jpg")
        self.assertNotContains(response, "<img")

    def test_registration_creates_user_and_student_profile(self):
        response = self.client.post(reverse("register"), data={
            "username": "student123",
            "password1": "N7vQp4x!",
            "password2": "N7vQp4x!",
        })

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="student123")
        self.assertTrue(user.check_password("N7vQp4x!"))
        self.assertTrue(hasattr(user, "studentprofile"))

    def test_authenticated_user_is_redirected_away_from_registration(self):
        user = User.objects.create_user(username="student123", password="N7vQp4x!")
        self.client.force_login(user)

        response = self.client.get(reverse("register"))

        self.assertRedirects(response, reverse("onboarding"))

    def test_logout_redirects_to_registration_page(self):
        user = User.objects.create_user(username="student123", password="N7vQp4x!")
        self.client.force_login(user)

        response = self.client.post(reverse("logout"), follow=True)

        self.assertRedirects(response, reverse("register"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Create your account")

    def test_login_page_matches_image_free_dashboard_theme(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="auth-card"')
        self.assertContains(response, "--bg: #050505")
        self.assertContains(response, "background: var(--solid)")
        self.assertNotContains(response, "login-photo.jpg")
        self.assertNotContains(response, "<img")

    def test_sign_in_shows_login_page_even_when_a_session_exists(self):
        user = User.objects.create_user(username="student123", password="N7vQp4x!")
        self.client.force_login(user)

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")
        self.assertContains(response, 'class="btn-signin"')

    def test_stale_login_csrf_token_returns_to_sign_in(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("login"))

        response = client.post(reverse("login"), {
            "username": "student123",
            "password": "N7vQp4x!",
            "csrfmiddlewaretoken": "stale-token",
        }, follow=True)

        self.assertRedirects(response, reverse("login"), status_code=302, target_status_code=200)
        self.assertContains(response, "That form expired")
        self.assertContains(response, "Welcome back")

    def test_valid_csrf_login_still_signs_in(self):
        User.objects.create_user(username="student123", password="N7vQp4x!")
        client = Client(enforce_csrf_checks=True)
        login_page = client.get(reverse("login"))
        token = str(login_page.context["csrf_token"])

        response = client.post(reverse("login"), {
            "username": "student123",
            "password": "N7vQp4x!",
            "csrfmiddlewaretoken": token,
        })

        self.assertRedirects(response, reverse("onboarding"))
