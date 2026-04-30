from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    university = models.CharField(max_length=255)
    bio = models.TextField(blank=True, default='')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'university']

    def __str__(self):
        return self.username
