from typing import Any

from django.contrib.auth.models import UserManager
from django.db import models

"""
IMPORTANT... NOTE that this only works for Queryset update() NOT bulk opretions.
at update time it overrides is_active based on disabled so that ban/unban/subsciption_disable work.
"""


class UserQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        if "disabled" in kwargs:
            kwargs["is_active"] = not kwargs["disabled"]
        return super().update(**kwargs)


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    pass


class EmployeeManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(parent__isnull=False)
