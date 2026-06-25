from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile


user = get_user_model()



@receiver(post_save, sender=user)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.parent is None:
            Profile.objects.create(owner=instance)
