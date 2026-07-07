from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from .managers import EmployeeManager, CustomUserManager
from common.models import UUIDModelMixin


class User(AbstractUser):
    email = models.EmailField(unique=True)
    pending_email = models.EmailField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    disabled = models.BooleanField(default=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee",
    )

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        """
        IMPORTANT... NOTE that this only works for save() not update() or bulk opretions.
        at save time it overrides is_active based on disabled so that ban/unban/subsciption_disable work.
        """
        self.is_active = not self.disabled
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.username}"


class Employee(User):
    objects = EmployeeManager()

    class Meta:
        proxy = True


class Profile(models.Model):
    owner = models.OneToOneField(
        User, blank=True, null=True, on_delete=models.CASCADE, related_name="profile"
    )
    number = models.CharField(max_length=15, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_address = models.TextField(null=True, blank=True)
    office_number1 = models.CharField(max_length=15, null=True, blank=True)
    office_number2 = models.CharField(max_length=15, null=True, blank=True)
    setting_mode = models.BooleanField(default=True)
    setting_reason = models.BooleanField(default=False)


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


class SubscriptionPlan(models.Model):
    Tier_Choices = [("silver", "Silver"), ("gold", "Gold")]
    Period_Choices = [
        ("monthly", "Monthly"),
        ("semi-annually", "Semi-Annually"),
        ("annually", "Annually"),
    ]

    tier = models.CharField(max_length=10, choices=Tier_Choices)
    period = models.CharField(max_length=20, choices=Period_Choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_plan_id = models.CharField(max_length=255, unique=True)
    max_employees = models.PositiveIntegerField(null=True, blank=True)
    max_services = models.PositiveIntegerField(null=True, blank=True)
    max_assignments_per_customer = models.PositiveIntegerField(null=True, blank=True)
    max_downloads = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-pk"]

    def __str__(self) -> str:
        return f"Tier: {self.tier} Period: {self.period}, Price: {self.price}"


class Subscription(models.Model):
    status_choices = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "cancelled"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True
    )
    razorpay_subscription_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    previous_razorpay_subscription_id = models.CharField(
        max_length=255, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=status_choices, default="trial")
    razorpay_status = models.CharField(max_length=50, null=True, blank=True)
    trial_end = models.DateTimeField()
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pk"]

    @property
    def is_active(self):
        """
        we do not check for status since even if subscription is cancelled,
        it can still be active until the end of the current period
        """
        now = timezone.now()
        if self.status == "trial":
            return now <= self.trial_end

        return self.current_period_end and self.current_period_end >= now

    @property
    def tier(self):
        if self.status == "trial":
            return "silver"

        return self.subscription_plan.tier if self.subscription_plan else None

    def __str__(self) -> str:
        return f"User: {self.user}, plan: {self.subscription_plan}, razorpay_subscription_id: {self.razorpay_subscription_id}"


class RazorpayEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-processed_at"]


class SubscriptionHistory(models.Model):
    subscription = models.ForeignKey(
        Subscription, related_name="payments", on_delete=models.CASCADE
    )
    razorpay_payment_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    processed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30)

    class Meta:
        ordering = ["-processed_at"]


class TemporaryPendingPlanChange(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    new_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    employee_id = models.JSONField(null=True, blank=True)
    service_id = models.JSONField(null=True, blank=True)
    customer_employee_id = models.JSONField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
