from django.conf import settings
from django.core.mail import send_mail
from rest_framework.exceptions import APIException


class EmailSendFailed(APIException):
    status_code = 503
    default_detail = "Could not send email. Changes were not saved."
    default_code = "email_send_failed"


def send_mail_or_raise(**kwargs):
    try:
        sent_count = send_mail(fail_silently=False, **kwargs)
    except Exception as exc:
        raise EmailSendFailed() from exc

    if sent_count != 1:
        raise EmailSendFailed()
    return sent_count


def send_otp_email_registration(otp, user):
    return send_mail_or_raise(
        subject="Verify your email - Hallmark Manager",
        message=f"Hi {user.username}, your OTP is: {otp}. expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Hi {user.username}</h2>
                    <p>Use this OTP to verify your account:</p>
                    <div style="font-size: 36px; font-weight: bold; letter-spacing: 10px;
                            padding: 20px; background: #f5f5f5; text-align: center;">
                    {otp}
                    </div>
                <p>Expires in <strong>10 minutes</strong>. If you did not create an account, you can safely ignore this email.</p>
            
                </div>
""",
    )


def send_otp_email_change(otp, user):
    return send_mail_or_raise(
        subject="Verify your new email - Hallmark Manager",
        message=f"Hi {user.username}, your OTP is: {otp}. expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.pending_email],
        html_message=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Hi {user.username}</h2>
                    <p>Use this OTP to verify your Email:</p>
                    <div style="font-size: 36px; font-weight: bold; letter-spacing: 10px;
                            padding: 20px; background: #f5f5f5; text-align: center;">
                    {otp}
                    </div>
                <p>Expires in <strong>10 minutes</strong>. If you did not request this email change, no action is 
                    required and your current email address will remain unchanged.</p>
            
                </div>
""",
    )


# If you did not request a password reset, please ignore this email and consider reviewing your account security.


def send_verified_email(user):
    return send_mail(
        subject="Account verified - Hallmark Manager",
        message=f"Hi {user.username}, your account has been verified.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Hi {user.username}</h2>
                    <p>Your account has been <strong>successfully verified</strong>.</p>
                    <p>Welcome to Hallmark Manager!</p>
                    <p>A clean workspace for your daily workflow.</p>
                </div>
                """,
    )
