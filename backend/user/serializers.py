# cls
from .models import User, Employee, Profile, UserOTP, SubscriptionPlan, Subscription
from core.models import Customer
from core.nestedserializer import NestedCustomerSerializer
from .Services.subscriptionlimit import PlanLimitChecker

# import cls
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer, UserDetailsSerializer

# tools
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "number",
            "company_name",
            "company_address",
            "office_number1",
            "office_number2",
            "setting_mode",
            "setting_reason",
        )

    def validate(self, attrs):
        user = self.context["request"].user
        if user.parent:
            raise ValidationError("Employee cannot create profile.")
        return attrs


class CustomCookieOnlyJwtSerializer(JWTSerializer):
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response.pop("access", None)
        response.pop("refresh", None)
        return response


class CustomRegisterSerializer(RegisterSerializer):
    number = serializers.CharField(max_length=15, required=True, allow_blank=True)
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

    # things like username, password, email are already handle by dj_rest_auth we just need to set what is not!!!

    def validate_email(self, email):
        email = email.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)
            user.is_active = False
            user.save()

            Profile.objects.create(
                owner=user,
                number=self.validated_data.get("number", ""),
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
        user_otp = UserOTP.objects.filter(
            user=user, task=UserOTP.Task.EMAIL_VERIFICATION
        ).first()

        if not user_otp:
            raise serializers.ValidationError(
                {"otp": "No OTP found. Please register again."}
            )

        if user_otp.failed_attempts >= 3:
            raise serializers.ValidationError(
                {"otp": "Maximum OTP attempts exceeded. Request a new OTP."}
            )

        # 4. Expired?
        if not user_otp.is_valid():
            raise serializers.ValidationError(
                {"otp": "OTP expired. Please request a new OTP."}
            )

        # 5. Match?
        if not check_password(attrs["otp"], user_otp.otp):
            user_otp.failed_attempts = F("failed_attempts") + 1
            user_otp.save(update_fields=["failed_attempts"])
            user_otp.refresh_from_db(fields=["failed_attempts"])

            raise serializers.ValidationError({"otp": "Invalid OTP."})

        attrs["user"] = user
        attrs["user_otp"] = user_otp
        return attrs


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    tier = serializers.CharField(source="get_tier_display", read_only=True)
    period = serializers.CharField(source="get_period_display", read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "tier",
            "period",
            "price",
            "max_employees",
            "max_services",
            "max_assignments_per_customer",
            "max_downloads",
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display", read_only=True)
    subscription_plan = SubscriptionPlanSerializer()

    class Meta:
        model = Subscription
        fields = [
            "status",
            "subscription_plan",
            "current_period_start",
            "current_period_end",
        ]
        read_only_fields = fields


class UserSerializer(UserDetailsSerializer):
    profile = ProfileSerializer(required=False, allow_null=True)
    email = serializers.EmailField(required=True)
    subscription = SubscriptionSerializer(read_only=True)
    is_parent = serializers.SerializerMethodField()

    class Meta(UserDetailsSerializer.Meta):
        fields = (
            "public_id",
            "username",
            "email",
            "profile",
            "subscription",
            "is_parent",
        )

    def get_is_parent(self, obj):
        return obj.parent_id is None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.parent_id is not None:
            data.pop("profile", None)
            data.pop("subscription", None)

        return data

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate_email(self, email):
        email = email.strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def update(self, instance, validated_data):
        profile_data = validated_data.get("profile", None)
        email = validated_data.get("email", instance.email)

        if instance.email != email:
            instance.username = validated_data.get("username", instance.username)
            instance.pending_email = email
            instance.email_verified = False
            instance.save()

        else:
            instance.username = validated_data.get("username", instance.username)
            instance.email = validated_data.get("email", instance.email)

            instance.save()

        if profile_data is None:
            return instance

        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)

        profile.save()

        return instance


class ChangeEmailOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):

        # get user from contexts
        user = self.context["request"].user

        # check already verified
        if not user.pending_email:
            raise serializers.ValidationError({"email": "No pending email to verify."})

        # get the latest otp for this user from system
        user_otp = UserOTP.objects.filter(
            user=user, task=UserOTP.Task.EMAIL_CHANGE
        ).first()

        if not user_otp:
            raise serializers.ValidationError(
                {"otp": "No OTP found. Please try again later."}
            )

        if user_otp.failed_attempts >= 3:
            raise serializers.ValidationError(
                {"otp": "Maximum OTP attempts exceeded. Request a new OTP."}
            )

        # 4. Expired?
        if not user_otp.is_valid():
            raise serializers.ValidationError(
                {"otp": "OTP expired. Please request a new OTP."}
            )

        # 5. Match?
        if not check_password(attrs["otp"], user_otp.otp):
            user_otp.failed_attempts = F("failed_attempts") + 1
            user_otp.save(update_fields=["failed_attempts"])
            user_otp.refresh_from_db(fields=["failed_attempts"])

            raise serializers.ValidationError({"otp": "Invalid OTP."})

        attrs["user"] = user
        attrs["user_otp"] = user_otp
        return attrs


class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    class Meta:
        model = Employee
        fields = [
            "public_id",
            "username",
            "password",
            "re_password",
            "email",
        ]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        password = attrs.get("password", None)
        re_password = attrs.pop("re_password", None)
        user = self.context["request"].user

        if user.parent:
            raise ValidationError({"message": "Employee can not create employees."})

        if password != re_password:
            raise ValidationError({"message": "Password do not match."})

        attrs["parent"] = user

        PlanLimitChecker(user).assert_can_add_employee()

        return attrs

    def create(self, validated_data):

        password = validated_data.pop("password", None)

        employee = Employee.objects.create(**validated_data)
        employee.is_active = False
        employee.email_verified = False
        employee.set_password(password)
        employee.save()

        return employee


class ReadOnlyEmployeeSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "public_id",
            "username",
            "email",
            "is_active",
            "disabled",
            "customer",
        ]
        read_only_fields = fields

    def get_customer(self, obj):
        assignment = getattr(obj, "active_assignment", [])
        return NestedCustomerSerializer(
            [a.customer for a in assignment], many=True
        ).data


class Sync_Employee_Customer(serializers.Serializer):
    customer = serializers.SlugRelatedField(
        slug_field="public_id", many=True, queryset=Customer.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            self.fields["customer"].queryset = Customer.objects.filter(owner=user)
        else:
            self.fields["customer"].queryset = Customer.objects.none()


class NestedEmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = [
            "public_id",
            "username",
            "email",
            "is_active",
            "disabled",
        ]
        read_only_fields = fields
