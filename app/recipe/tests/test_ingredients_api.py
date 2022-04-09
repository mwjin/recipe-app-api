from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        resp = self.client.get(INGREDIENTS_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the authorized user ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass1234",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=self.user, name="Egg")
        Ingredient.objects.create(user=self.user, name="Bacon")

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_retrieve_ingredients_limited_to_user(self):
        """Test that returned ingredients are for the authenticated user"""
        another_user = get_user_model().objects.create_user(
            "test2@test.com",
            "test2pass1234",
        )
        Ingredient.objects.create(user=self.user, name="Egg")
        Ingredient.objects.create(user=self.user, name="Bacon")
        Ingredient.objects.create(user=another_user, name="Rice")

        ingredients = (
            Ingredient.objects.all().order_by("-name").filter(user=self.user)
        )
        serializer = IngredientSerializer(ingredients, many=True)

        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {"name": "Test"}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating a new ingredient with invalid payload"""
        payload = {"name": ""}
        resp = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
