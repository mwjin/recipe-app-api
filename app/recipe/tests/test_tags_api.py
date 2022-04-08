from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        resp = self.client.get(TAGS_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass1234",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Drunken")

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        resp = self.client.get(TAGS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """Test that returned tags are for the authenticated user"""
        another_user = get_user_model().objects.create_user(
            "test2@test.com",
            "test2pass1234",
        )
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Drunken")
        Tag.objects.create(user=another_user, name="Meaty")

        tags = Tag.objects.all().order_by("-name").filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        resp = self.client.get(TAGS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)
