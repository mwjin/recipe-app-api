from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class TestAdminSite(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="admintest1234"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="user1@test.com", password="user1test1234", name="User1"
        )

    def test_user_listed(self):
        """Test that users are listed on user page"""
        url = reverse("admin:core_user_changelist")
        resp = self.client.get(url)

        self.assertContains(resp, self.user.email)
        self.assertContains(resp, self.user.name)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        url = reverse("admin:core_user_change", args=[self.user.id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_create_user_page(self):
        """Test that the create user page works"""
        url = reverse("admin:core_user_add")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
