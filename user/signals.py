from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, UserSubscription
from django.utils import timezone
from datetime import timedelta

user = get_user_model()



@receiver(post_save, sender=user)
def create_trial_plan(sender, instance, created, **kwargs):
    if created:
        if instance.parent is None:
            trial_end = timezone.now() + timedelta(days=30)
            UserSubscription.objects.create(
                user=instance,
                status="trial",
                trial_end=trial_end,
            )
