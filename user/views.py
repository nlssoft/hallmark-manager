from dj_rest_auth.registration.views import RegisterView
from rest_framework.views import APIView
from .Services.helper_functions import (
    create_otp_for_email_verification,
    create_otp_for_password_reset,
)
from .Services.emails import send_otp_email, send_verified_email
from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import VerifyEmailOTPSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.core.cache import cache
from django.utils import timezone
from .models import UserOTP
from .Services.throttles import OTPCooldownThrottling

today = timezone.now().date()


class CustomRegisterView(RegisterView):

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save(self.request)
            user.is_active = False
            user.save()

            otp = create_otp_for_email_verification(user)
            send_otp_email(otp, user)

            return Response(
                {
                    "message": "OTP sent to your email. Please verify to complete signup."
                },
                status=status.HTTP_201_CREATED,
            )


class VerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        otp_obj = serializer.validated_data["otp_obj"]

        otp_obj.used = True
        otp_obj.save()

        user.is_active = True
        user.email_verified = True  # ← both, for the reason below
        user.save()

        send_verified_email(user)
        return Response({"message": "Account verified. You can now log in."})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPCooldownThrottling]

    def get(self, request):
        return Response({"message": "Use POST to verify OTP"})

    def post(self, request):
        email = request.data.get("email", "").strip()
        user = User.objects.filter(
            email=email,
            is_active=False,
            email_verified=False,
        ).first()

        if not user:
            return Response(
                {"message": "If an account exists, an OTP has been sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today_otp_count = UserOTP.objects.filter(
            user=user,
            task=UserOTP.Task.EMAIL_VERIFICATION,
            for_otp__created_at__date=today,
        ).count()

        if today_otp_count >= 3:
            return Response(
                {"message": "Daily OTP limit reached. Try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = create_otp_for_email_verification(user)
        send_otp_email(otp, user)
        return Response({"message": "If an account exists, an OTP has been sent."})
