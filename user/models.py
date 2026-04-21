from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email= models.EmailField(unique=True)
    company_name = models.CharField(max_length=500)
    phone_number= models.CharField(max_length=255)
    address= models.TextField()
    parent=models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='Employee',
    )

    class Meta:
        ordering=['-pk']