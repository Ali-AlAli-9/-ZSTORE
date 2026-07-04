from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import override_settings

User = get_user_model()


class RegisterTest(APITestCase):
    @patch("users.views.send_email")
    def test_register_success_returns_tokens(self, mock_send):
        response = self.client.post(
            "/users/register/",
            {"username": "newuser", "email": "a@a.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh_token", response.cookies)
        self.assertIsNotNone(response.cookies["refresh_token"].value)

    def test_register_missing_password_fails(self):
        response = self.client.post(
            "/users/register/", {"username": "newuser", "email": "a@a.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username_fails(self):
        User.objects.create_user(username="user1", password="pass123")
        response = self.client.post(
            "/users/register/",
            {"username": "user1", "password": "pass456"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(APITestCase):
    def setUp(self):
        User.objects.create_user(username="testuser", password="testpass123")

    def test_login_success_returns_tokens(self):
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            "/users/login/", {"username": "testuser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTest(APITestCase):
    def test_logout_requires_refresh_token(self):
        user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.post("/users/logout/", {"refresh": "invalid"})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_unauthenticated_cannot_logout(self):
        response = self.client.post("/users/logout/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListTest(APITestCase):
    def test_admin_can_list_users(self):
        admin = User.objects.create_superuser(username="admin", password="pass")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normal_user_cannot_list_users(self):
        user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegisterEmailTest(APITestCase):
    @patch("users.views.send_email")
    def test_register_sends_verification_email(self, mock_send):
        response = self.client.post(
            "/users/register/",
            {"username": "testuser", "email": "testuser@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        self.assertIn("Verify your email", args[0])
        self.assertIn("testuser@example.com", args[3])
        self.assertIn("localhost:5173/verify/", args[1])

    @patch("users.views.send_email")
    def test_register_without_email_does_not_send(self, mock_send):
        response = self.client.post(
            "/users/register/",
            {"username": "nouser", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send.assert_not_called()

    @patch("users.views.send_email")
    def test_email_contains_verify_url(self, mock_send):
        response = self.client.post(
            "/users/register/",
            {"username": "emailuser", "email": "emailuser@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        self.assertIn("localhost:5173/verify/", args[1])


@override_settings(REST_FRAMEWORK={"EMAIL_THROTTLE_RATE": "1000/minute", "DEFAULT_THROTTLE_RATES": {"anon": "60/hour", "user": "10000/hour", "email": "1000/minute"}})
class UpdateEmailTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")

    def _patch_throttle(self):
        patcher = patch("users.views.EmailThrottle.allow_request", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_unauthenticated_cannot_update(self):
        response = self.client.post("/users/update-email/", {"email": "a@a.com"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("users.views.send_email")
    def test_update_email_sends_verification(self, mock_send):
        self._patch_throttle()
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/users/update-email/", {"email": "new@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertFalse(self.user.is_email_verified)
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        self.assertIn("new@example.com", args[3])

    def test_update_duplicate_email_fails(self):
        self._patch_throttle()
        User.objects.create_user(username="other", email="existing@a.com", password="pass")
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/users/update-email/", {"email": "existing@a.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_empty_email_fails(self):
        self._patch_throttle()
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/users/update-email/", {"email": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("users.views.send_email")
    def test_update_same_email_resends_verification(self, mock_send):
        self.user.email = "same@a.com"
        self.user.is_email_verified = True
        self.user.save()
        self._patch_throttle()
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/users/update-email/", {"email": "same@a.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        mock_send.assert_called_once()