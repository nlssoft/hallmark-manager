from user.models import OTP, UserOTP
from django.utils import timezone
import secrets


def create_otp_for_email_verification(user):
    otp_code = str(secrets.randbelow(900000) + 100000)
    otp = OTP.objects.create(
        otp=otp_code,
        expired_at=timezone.now() + timezone.timedelta(minutes=10),
    )
    UserOTP.objects.create(user=user, for_otp=otp, task=UserOTP.Task.EMAIL_VERIFICATION)
    return otp_code


def create_otp_for_password_reset(user):
    otp_code = str(secrets.randbelow(900000) + 100000)
    otp = OTP.objects.create(
        otp=otp_code,
        expired_at=timezone.now() + timezone.timedelta(minutes=2),
    )
    UserOTP.objects.create(user=user, for_otp=otp, task=UserOTP.Task.PASSWORD_RESET)
    return otp_code
