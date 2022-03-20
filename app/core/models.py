from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class MyUserManager(BaseUserManager):
    """Manager for my custom user model"""

    def create_user(self, email, password=None):
        """Creates a new user"""
        if not email:
            raise ValueError("User must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and save a new superuser with given details"""
        user = self.create_user(email, password)
        user.is_admin = True
        user.save(using=self._db)

        return user


class MyUser(AbstractBaseUser):
    """Database model for users in the system"""

    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        """Returning string representation of our user"""
        return self.email

    @property
    def is_staff(self):
        return self.is_admin
