from django.db import models


class EmployeeManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(parent__isnull=False)
