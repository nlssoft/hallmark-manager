from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    parent = models.ForeignKey(
        "self",0258*.369
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="Employee",
    )

    class Meta:
        ordering = ["-pk"]


class OtpVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        expiry=self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() < expiry and not self.is_verified
        
    def __str__(self):
        return f"OTP for {self.user.username}"
369