from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out
)

from django.dispatch import receiver

from django.utils import timezone

from .models import UserProfile


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    profile.is_online = True

    profile.save()


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):

    if user is None:
        return

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    profile.is_online = False

    profile.last_seen = timezone.now()

    profile.save()