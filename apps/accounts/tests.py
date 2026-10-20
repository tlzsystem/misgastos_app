from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(
    RECAPTCHA_ENABLED=True,
    RECAPTCHA_SITE_KEY="test_site_key",
    RECAPTCHA_SECRET_KEY="test_secret_key",
)
class ReCaptchaAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="carlos",
            email="carlos@example.com",
            password="SecurePass123!",
        )

    def test_login_blocked_without_recaptcha_token(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "carlos",
                "password": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No soy un robot")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    @patch("apps.accounts.forms.verify_recaptcha_token", return_value=True)
    def test_login_succeeds_with_valid_recaptcha_token(self, mock_verify):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "carlos",
                "password": "SecurePass123!",
                "g-recaptcha-response": "valid-token",
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_verify.assert_called_once()

    def test_register_blocked_without_recaptcha_token(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "nuevousuario",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "email": "nuevo@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No soy un robot")
        self.assertFalse(User.objects.filter(username="nuevousuario").exists())

    @patch("apps.accounts.forms.verify_recaptcha_token", return_value=True)
    def test_register_succeeds_with_valid_recaptcha_token(self, mock_verify):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "nuevousuario",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "email": "nuevo@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "create_default_categories": True,
                "g-recaptcha-response": "valid-token",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="nuevousuario").exists())
        mock_verify.assert_called_once()
