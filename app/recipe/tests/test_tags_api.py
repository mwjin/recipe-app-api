from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
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

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {"name": "Test"}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload"""
        payload = {"name": ""}
        resp = self.client.post(TAGS_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="Tag 1")
        tag2 = Tag.objects.create(user=self.user, name="Tag 2")
        recipe = Recipe.objects.create(
            title="Recipe 1",
            time_minutes=10,
            price=5.00,
            user=self.user,
        )
        recipe.tags.add(tag1)

        resp = self.client.get(TAGS_URL, {"assigned_only": 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, resp.data)
        self.assertNotIn(serializer2.data, resp.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name="Tag 1")
        Tag.objects.create(user=self.user, name="Tag 2")
        recipe1 = Recipe.objects.create(
            title="Pancakes",
            time_minutes=5,
            price=3.00,
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="Cheese cakes",
            time_minutes=10,
            price=7.00,
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        resp = self.client.get(TAGS_URL, {"assigned_only": 1})
        self.assertEqual(len(resp.data), 1)
