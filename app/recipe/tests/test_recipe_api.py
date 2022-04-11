import os
import tempfile

from core.models import Ingredient, Recipe, Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="Sample Tag"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Sample Ingredient"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": 5.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        resp = self.client.get(RECIPES_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the authorized user recipe API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass1234",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        resp = self.client.get(RECIPES_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_retrieve_recipes_limited_to_user(self):
        """Test that returned ingredients are for the authenticated user"""
        another_user = get_user_model().objects.create_user(
            "test2@test.com",
            "test2pass1234",
        )
        sample_recipe(user=self.user)
        sample_recipe(user=another_user)

        recipes = Recipe.objects.all().order_by("-title").filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        resp = self.client.get(RECIPES_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        url = detail_url(recipe.id)
        resp = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a new basic recipe"""
        payload = {
            "title": "Fried Chicken",
            "time_minutes": 60,
            "price": 15.00,
        }
        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data["id"])
        for k, v in payload.items():
            self.assertEqual(v, getattr(recipe, k))

    def test_create_recipe_with_tag(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(self.user, "Tag1")
        tag2 = sample_tag(self.user, "Tag2")

        payload = {
            "title": "Cheese Cake",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 30,
            "price": 20.00,
        }

        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(self.user, "Egg")
        ingredient2 = sample_ingredient(self.user, "Salt")

        payload = {
            "title": "Fried Egg",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 5,
            "price": 2.00,
        }

        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_create_recipe_with_other_user_tag(self):
        """Test creating a recipe with other_user_tag"""
        another_user = get_user_model().objects.create_user(
            "test2@test.com",
            "test2pass1234",
        )
        tag1 = sample_tag(self.user, "Tag1")
        tag2 = sample_tag(another_user, "Tag2")

        payload = {
            "title": "Cheese Cake",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 30,
            "price": 20.00,
        }

        resp = self.client.post(RECIPES_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_invalid(self):
        """Test creating a new recipe with invalid payload"""
        payload = {
            "title": "",
            "time_minutes": 60,
            "price": 15.00,
        }
        resp = self.client.post(RECIPES_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_recipe(self):
        """Test updating a recipe with PATCH method"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name="Old"))
        new_tag = sample_tag(user=self.user, name="New")

        payload = {"title": "Chicken", "tags": [new_tag.id]}
        resp = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with PUT method"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name="Old"))

        payload = {"title": "Chicken", "time_minutes": 25, "price": 14.00}
        resp = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])
        self.assertEqual(len(recipe.tags.all()), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass1234",
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            resp = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("image", resp.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        resp = self.client.post(url, {"image": "no_image"}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
