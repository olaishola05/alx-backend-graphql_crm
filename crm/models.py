from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user = models.UUIDField(default=uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    def __str__(self):
        return self.username
