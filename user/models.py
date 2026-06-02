from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="Employee",
    )

    class Meta:
        ordering = ["-pk"]


class OtpVerification(models.Model):
    EMAIL = "email"
    PASSWORD_RESET = "password_reset"

    TASK_CHOICES = [
        (EMAIL, "Email Verification"),
        (PASSWORD_RESET, "Password Reset"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="otp_verification"
    )
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    task = models.CharField(
        max_length=20,
        choices=TASK_CHOICES,
    )

    def is_valid(self):
        return timezone.now() < self.expires_at and not self.is_used

    def __str__(self):
        return f"OTP for {self.user.username}"
