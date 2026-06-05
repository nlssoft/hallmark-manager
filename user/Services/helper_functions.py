from user.models import UserOTP
from django.utils import timezone
import secrets
from django.contrib.auth.hashers import make_password
from django.db import transaction


def create_otp(user, task, expires_in_minutes=10):
    otp_code = str(secrets.randbelow(900000) + 100000)
    with transaction.atomic():
        UserOTP.objects.filter(user=user, task=task, used=False).update(used=True)
        UserOTP.objects.create(
            user=user,
            otp=make_password(otp_code),
            expired_at=timezone.now() + timezone.timedelta(minutes=expires_in_minutes),
            task=task,
        )
    return otp_code


def create_otp_for_email_verification(user):
    return create_otp(user, UserOTP.Task.EMAIL_VERIFICATION)


def create_otp_for_password_reset(user):
    return create_otp(user, UserOTP.Task.PASSWORD_RESET, expires_in_minutes=2)


def create_otp_for_email_change(user):
    return create_otp(user, UserOTP.Task.EMAIL_CHANGE)


def create_otp_for_password_update(user):
    return create_otp(user, UserOTP.Task.PASSWORD_RESET, expires_in_minutes=2)
