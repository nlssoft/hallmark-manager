from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)
    pending_email = models.EmailField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="Employee",
    )

    class Meta:
        ordering = ["-pk"]


class UserOTP(models.Model):
    class Task(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", "Email Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"
        EMAIL_CHANGE = "email_change", "Email Change"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_otps"
    )
    task = models.CharField(max_length=20, choices=Task.choices)
    otp = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()  # set at creation: now + 10min
    used = models.BooleanField(default=False)
    failed_attempts = models.PositiveIntegerField(default=0)

    def is_valid(self):
        return not self.used and timezone.now() < self.expired_at

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.task}"
