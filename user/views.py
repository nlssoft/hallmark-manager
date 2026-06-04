from django.db import transaction
from django.utils import timezone
from dj_rest_auth.registration.views import RegisterView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


from .models import User, UserOTP
from .serializers import VerifyEmailOTPSerializer
from .Services.emails import (
    send_otp_email_registration,
    send_verified_email,
    send_otp_email_change,
)
from .Services.helper_functions import (
    create_otp_for_email_verification,
    create_otp_for_email_change,
    create_otp_for_password_reset,
)
from .Services.throttles import OTPCooldownThrottling
from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.views import UserDetailsView

BaseRefreshView = get_refresh_view()


class CustomCookieTokenRefreshView(BaseRefreshView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code == 200:
            response.data.pop("access", None)
            response.data.pop("refresh", None)
        return response


class CustomRegisterView(RegisterView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save(self.request)
            otp = create_otp_for_email_verification(user)
            send_otp_email_registration(otp, user)

        return Response(
            {"message": "OTP sent to your email. Please verify to complete signup."},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user_otp = serializer.validated_data["user_otp"]

        user_otp.used = True
        user_otp.save(update_fields=["used"])

        user.is_active = True
        user.email_verified = True
        user.save(update_fields=["is_active", "email_verified"])

        send_verified_email(user)
        return Response({"message": "Account verified. You can now log in."})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPCooldownThrottling]

    def get(self, request):
        return Response({"message": "Use POST to resend OTP."})

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        user = User.objects.filter(
            email=email,
            is_active=False,
            email_verified=False,
        ).first()

        if not user:
            return Response(
                {"message": "If an account exists, an OTP has been sent."},
                status=status.HTTP_200_OK,
            )

        today_otp_count = UserOTP.objects.filter(
            user=user,
            task=UserOTP.Task.EMAIL_VERIFICATION,
            created_at__date=timezone.now().date(),
        ).count()

        if today_otp_count >= 3:
            return Response(
                {"message": "Daily OTP limit reached. Try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = create_otp_for_email_verification(user)
        send_otp_email_registration(otp, user)
        return Response(
            {"message": "If an account exists, an OTP has been sent."},
            status=status.HTTP_200_OK,
        )


class CustomUserDetailView(UserDetailsView):

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_excetion=True)

        with transaction.atomic():
            user = serializer.save(self.request)
            if user.pending_email:
                otp = create_otp_for_email_change(user)
                send_otp_email_change(otp, user)
                return Response(
                    {
                        "message": "Profile updated. An OTP has been sent to your new email address to verify the change."
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"message": "Profile updated successfully."},
                    status=status.HTTP_200_OK,
                )
