from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")


def create_user(**param):
    return get_user_model().objects.create_user(**param)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "email": "test@test.com",
            "password": "testpass1234",
            "name": "Test User",
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**resp.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", resp.data)

    def test_user_already_exists(self):
        """Test creating user that already exists fails"""
        payload = {
            "email": "test@test.com",
            "password": "testpass1234",
        }
        create_user(**payload)
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters"""
        payload = {
            "email": "test2@test.com",
            "password": "1234",
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for user"""
        payload = {
            "email": "test@test.com",
            "password": "testpass1234",
        }
        create_user(**payload)
        resp = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credential(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email="test@test.com", password="testpass1234")
        payload = {
            "email": "test@test.com",
            "password": "wrong",
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user does not exist"""
        payload = {
            "email": "test@test.com",
            "password": "testpass1234",
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_password(self):
        """Test that password is required"""
        resp = self.client.post(TOKEN_URL, {"email": "test@test.com"})
        self.assertNotIn("token", resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_email(self):
        """Test that email is required"""
        resp = self.client.post(TOKEN_URL, {"password": "12345667qqwe!"})
        self.assertNotIn("token", resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
