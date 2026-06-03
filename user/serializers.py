# cls
from .models import User, OTP, UserOTP
from core.models import Profile

# import cls
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer

# tools
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F


class CustomeCookieOnlyJwtSerializer(JWTSerializer):
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response.pop("access", None)
        response.pop("refresh", None)
        return response


class CustomeRegisterSerializer(RegisterSerializer):
    number = serializers.CharField(max_length=15)
    company_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    company_address = serializers.CharField(
        max_length=600, required=False, allow_blank=True
    )
    office_number1 = serializers.CharField(
        max_length=15, required=False, allow_blank=True
    )
    office_number2 = serializers.CharField(
        max_length=15, required=False, allow_blank=True
    )
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    # things like username, password, email are already handle by dj_rest_auth we just need to set what is not!!!

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)

            user.first_name = self.validated_data["first_name"]
            user.last_name = self.validated_data["last_name"]
            user.is_active = False
            user.save()

            Profile.objects.create(
                owner=user,
                number=self.validated_data["number"],  # required, safe
                company_name=self.validated_data.get("company_name", ""),
                company_address=self.validated_data.get("company_address", ""),
                office_number1=self.validated_data.get("office_number1", ""),
                office_number2=self.validated_data.get("office_number2", ""),
            )

            return user


class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):

        # check user exists
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found."})

        # check already verified
        if user.email_verified:
            raise serializers.ValidationError({"email": "Email is already verified."})

        # get the latest otp for this user from system
        user_otp = (
            UserOTP.objects.filter(user=user, task=UserOTP.Task.EMAIL_VERIFICATION)
            .select_related("for_otp")
            .first()
        )

        if not user_otp:
            raise serializers.ValidationError(
                {"otp": "No OTP found. Please register again."}
            )

        otp_obj = user_otp.for_otp

        if otp_obj.failed_attempts >= 3:
            raise serializers.ValidationError(
                {"otp": "Maximum OTP attempts exceeded. Request a new OTP."}
            )

        # 4. Expired?
        if not otp_obj.is_valid():
            raise serializers.ValidationError(
                {"otp": "OTP expired. Please request a new OTP."}
            )

        # 5. Match?
        if otp_obj.otp != attrs["otp"]:
            otp_obj.failed_attempts = F("failed_attempts") + 1
            otp_obj.save(update_fields=["failed_attempts"])
            otp_obj.refresh_from_db(fields=["failed_attempts"])
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs
