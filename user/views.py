from django.db import transaction
from django.utils import timezone
from dj_rest_auth.registration.views import RegisterView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.filters import SearchFilter


from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from core.permissions import ParentAccount_Only
from core.models import Customer
from .models import User, UserOTP, Employee
from .serializers import (
    VerifyEmailOTPSerializer,
    ChangeEmailOTPSerializer,
    EmployeeSerializer,
    Sync_Employee,
)
from .Services.emails import (
    send_otp_email_registration,
    send_verified_email,
    send_otp_email_change,
)
from .Services.helper_functions import (
    create_otp_for_email_verification,
    create_otp_for_email_change,
)
from .Services.throttles import OTPCooldownThrottling
from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.views import UserDetailsView
from rest_framework.decorators import action


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
                {
                    "message": "OTP sent to your email. Please verify to complete signup."
                },
                status=status.HTTP_201_CREATED,
            )


class VerifyEmailOTPView(generics.GenericAPIView):
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


class ResendVerifyEmailOTPView(APIView):
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
        with transaction.atomic():
            partial = kwargs.pop("partial", False)
            instance = self.get_object()  # ← get the user
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            new_email = serializer.validated_data.get("email")
            email_changed = new_email is not None and instance.email != new_email

            user = serializer.save()
            if email_changed:
                otp = create_otp_for_email_change(user)
                send_otp_email_change(otp, user)
                return Response(
                    {
                        "message": "Profile updated. An OTP has been sent to your new email address to verify the updated email."
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    self.get_serializer(user).data,
                    status=status.HTTP_200_OK,
                )


class ResendChangeEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [OTPCooldownThrottling]

    def get(self, request):
        return Response({"message": "Use POST to resend OTP."})

    def post(self, request):
        user = request.user

        today_otp_count = UserOTP.objects.filter(
            user=user,
            task=UserOTP.Task.EMAIL_CHANGE,
            created_at__date=timezone.now().date(),
        ).count()

        if today_otp_count >= 3:
            return Response(
                {"message": "Daily OTP limit reached. Try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = create_otp_for_email_change(user)
        send_otp_email_change(otp, user)
        return Response(
            {"message": "If an account exists, an OTP has been sent."},
            status=status.HTTP_200_OK,
        )


class ChangeEmailOTPView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangeEmailOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user_otp = serializer.validated_data["user_otp"]

        user_otp.used = True
        user_otp.save(update_fields=["used"])

        user.email_verified = True
        user.email = user.pending_email
        user.pending_email = None
        user.save(update_fields=["email", "pending_email", "email_verified"])

        return Response({"message": "Account verified. You can now log in."})


class EmployeeView(
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = EmployeeSerializer
    permission_classes = [ParentAccount_Only]
    filter_backends = [SearchFilter]
    search_fields = ["username", "customer__name", "customer__logo"]

    def get_serializer_class(self):
        if self.action == "sync_employee":
            return Sync_Employee

        return EmployeeSerializer

    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Employee.objects.none()

        return Employee.objects.filter(parent=user).prefetch_related(
            "customer_set"
        ).order_by("id")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            otp = create_otp_for_email_verification(user)
            send_otp_email_registration(otp, user)

            return Response(
                {
                    "message": "OTP sent to your email. Please verify to complete signup."
                },
                status=status.HTTP_201_CREATED,
            )

    @action(detail=True, methods=["post"])
    def ban(self, request, pk=None):
        employee = self.get_object()

        employee.is_active = False
        employee.save(update_fields=["is_active"])

        # access is handle by simple jwt as it checks on every request -  user.is_active
        # refresh blaclisting is not needed but still the code below is profesniol cleanup.

        tokens = OutstandingToken.objects.filter(user=employee)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        return Response({"message": "Employee banned."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unban(self, request, pk=None):
        employee = self.get_object()

        employee.is_active = True
        employee.save(update_fields=["is_active"])

        return Response({"message": "Employee is unbanned."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="sync-employee")
    def sync_employee(self, request, pk=None):
        employee = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_id = {c.id for c in serializer.validated_data["customer"]}

        through = Customer.assigned_to.through

        through.objects.filter(user_id=employee.id).exclude(
            customer_id__in=new_id
        ).delete()

        existing = set(
            through.objects.filter(
                user_id=employee.id,
                customer_id__in=new_id
            ).values_list("customer_id", flat=True)
        )

        through.objects.bulk_create(
            [
                through(customer_id=cid, user_id=employee.id)
                for cid in (new_id - existing)
            ],
            ignore_conflicts=True,
        )


        return Response({"synced": len(new_id)})
