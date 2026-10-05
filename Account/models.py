from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)

    profile_image = models.ImageField(
        upload_to='profile',
        null=True,
        blank=True
    )

    is_email_verified = models.BooleanField(default=False)

    email_token = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.email or self.user.username