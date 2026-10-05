from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
import uuid

from .models import Profile
from verificationsystem.emails import send_account_activation_email


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return

    needs_verification = bool(instance.email) and not instance.is_superuser
    email_token = str(uuid.uuid4()) if needs_verification else None

    Profile.objects.create(
        user=instance,
        first_name=instance.first_name,
        last_name=instance.last_name,
        email=instance.email or None,
        email_token=email_token,
        is_email_verified=not needs_verification,
    )

    if needs_verification:
        send_account_activation_email(instance.email, email_token)