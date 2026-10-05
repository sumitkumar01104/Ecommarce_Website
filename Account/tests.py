from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Profile


class AccountAPITests(APITestCase):

    def setUp(self):
        self.email = "test@example.com"
        self.password = "Test@12345"

        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            first_name="Test",
            last_name="User",
        )

        # Profile is automatically created by signal
        self.profile = Profile.objects.get(
            user=self.user
        )

        self.profile.first_name = "Test"
        self.profile.last_name = "User"
        self.profile.is_email_verified = True

        self.profile.save(
            update_fields=[
                "first_name",
                "last_name",
                "is_email_verified",
            ]
        )

    def test_register_user(self):
        response = self.client.post(
            reverse("api_register"),
            {
                "first_name": "Sumit",
                "last_name": "Kumar",
                "email": "new@example.com",
                "password": "Strong@12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            User.objects.filter(
                email="new@example.com"
            ).exists()
        )

    def test_duplicate_email_rejected(self):
        response = self.client.post(
            reverse("api_register"),
            {
                "first_name": "Another",
                "last_name": "User",
                "email": self.email,
                "password": "Strong@12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_login_with_unverified_email_rejected(self):
        self.profile.is_email_verified = False
        self.profile.save(
            update_fields=["is_email_verified"]
        )

        response = self.client.post(
            reverse("api_login"),
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_login_with_verified_email(self):
        response = self.client.post(
            reverse("api_login"),
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "tokens",
            response.data
        )

        self.assertIn(
            "access",
            response.data["tokens"]
        )

        self.assertIn(
            "refresh",
            response.data["tokens"]
        )

    def test_login_invalid_password(self):
        response = self.client.post(
            reverse("api_login"),
            {
                "email": self.email,
                "password": "WrongPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_profile_authenticated(self):
        login_response = self.client.post(
            reverse("api_login"),
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK
        )

        access_token = login_response.data["tokens"]["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_logout_requires_refresh_token(self):
        login_response = self.client.post(
            reverse("api_login"),
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK
        )

        access_token = login_response.data["tokens"]["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            reverse("api_logout"),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )   