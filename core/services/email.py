from django.core.mail import send_mail
from django.conf import settings


def welcome_email(user):
    send_mail(
        subject="welcome",
        message=f"welcome {user.username}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
