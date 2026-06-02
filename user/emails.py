from django.core.mail import send_mail
from django.http import jsonresponse


def verified_email(request):
    send_mail(
        subject= 'Account verified',
        message= "Your account has been verified.",
        from_email= "Acme <onboarding@resend.dev>",
        recipient_list=["delivered@resend.dev"],
        html_message= "<p>Your account has been verified.</p>",
    )
    return jsonresponse({"message": "Email sent successfully"})


        




























#from urllib.parse import urlparse\';[p]
# from djoser.email import PasswordResetEmail
# from django.conf import settings


# class CustomPasswordResetEmail(PasswordResetEmail):
#     def get_context_data(self):
#         context = super().get_context_data()
#         frontend = urlparse(settings.FRONTEND_URL)

#         context["protocol"] = frontend.scheme
#         context["domain"] = frontend.netloc
#         context["url"] = f"reset-password/{context['uid']}/{context['token']}"
#         return context


