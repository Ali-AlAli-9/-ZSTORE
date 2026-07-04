from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager


class UserManager(BaseUserManager):
    def _create_user(self, username, email=None, password=None, **extra_fields):
        if email is not None:
            email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()