import json
import razorpay
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.permissions import ParentAccount_Only
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.db import transaction

from user.models import (
    Subscription,
    SubscriptionPlan,
    RazorpayEvent,
)
from .serializers import NestedEmployeeSerializer
from core.serializers import ServiceSerializer, ReadOnlyCustomerSerializer
from .Services.subscriptionserviceshelpers import SubscriptionHelperFN
from .models import Employee
from core.models import Customer, Service


from user.Services.subcriptionservices import (
    create_razorpay_subscription,
    handle_subscription_activated,
    handle_subscription_charged,
    handle_subscription_halted,
    handle_subscription_cancelled,
    handle_subscription_completed,
)
from .razorpay_client import client as razorpay


class SubscriptionPlanApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def get(self, request):
        plans = SubscriptionPlan.objects.all()

        data = [
            {
                "pk": p.pk,
                "tier": p.tier,
                "tier_display": p.get_tier_display(),
                "period": p.period,
                "period_display": p.get_period_display(),
                "price": str(p.price),
                "max_employess": str(p.max_employees),
                "max_services": str(p.max_services),
                "max_assignments_per_customer": str(p.max_assignments_per_customer),
            }
            for p in plans
        ]

        return Response(data, status=status.HTTP_200_OK)


class SubscriptionPlanPreviewApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def post(self, request):
        data = {}
        user = request.user
        plan_id = request.data.get("plan_id")

        try:
            new_plan = SubscriptionPlan.objects.get(pk=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Subscription plan is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["subscription_plan"] = {
            "pk": new_plan.pk,
            "tier": new_plan.tier,
            "tier_display": new_plan.get_tier_display(),
            "period": new_plan.period,
            "period_display": new_plan.get_period_display(),
            "price": str(new_plan.price),
            "max_employess": str(new_plan.max_employees),
            "max_services": str(new_plan.max_services),
            "max_assignments_per_customer": str(new_plan.max_assignments_per_customer),
        }

        # Upgrade
        if new_plan.tier == "gold":

            data["employee"] = list(
                Employee.objects.filter(parent=user, is_active=False)
            )
            data["service"] = list(Service.objects.filter(owner=user, disabled=True))
            data["customer"] = list(
                Customer.objects.filter(owner=user, active=False).prefetch_related(
                    "assigned_to"
                )
            )

        # DownGrade
        customer, employee, service = SubscriptionHelperFN.need_reducing(user, new_plan)

        data["bools"] = any((employee, service, customer))

        if employee:
            data["employee"] = NestedEmployeeSerializer(employee, many=True).data

        if service:
            data["service"] = ServiceSerializer(service, many=True).data

        if customer:
            data["customer"] = ReadOnlyCustomerSerializer(customer, many=True).data

        return Response(data, status=status.HTTP_200_OK)


class SubscriptionCreateApiView(APIView):
    permission_classes = [ParentAccount_Only]

    @transaction.atomic()
    def post(self, request):
        plan_id = request.data.get("plan_id")

        try:
            new_plan = SubscriptionPlan.objects.get(pk=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Subscription plan is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # this tells us what need reducing
        customer, employee, service = SubscriptionHelperFN.need_reducing(
            request.user, new_plan
        )

        # it checks that the data provied by user is acceptable or not. and creates a temporary row in tpc.
        SubscriptionHelperFN.create_temporary_plan_changes(
            customer, employee, service, request, new_plan
        )

        try:
            payment_data = create_razorpay_subscription(request.user, plan_id)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(payment_data, status=status.HTTP_201_CREATED)


class SubscritionStatusApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def get(self, request):
        try:
            sub = request.user.subscription
        except Subscription.DoesNotExist:
            return Response(
                {"error": "No subscription Found."}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "status": sub.status,
                "tier": sub.tier,
                "subscription_id": sub.razorpay_subscription_id,
                "is_active": sub.is_active,
                "trial_end": sub.trial_end,
                "current_period_end": sub.current_period_end,
                "plan": (
                    {
                        "tier": sub.subscription_plan.get_tier_display(),
                        "period": sub.subscription_plan.get_period_display(),
                        "price": str(sub.subscription_plan.price),
                    }
                    if sub.subscription_plan
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )


class SubscriptionCancelledApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def post(self, request):

        try:
            sub = request.user.subscription
        except Subscription.DoesNotExist:
            return Response(
                {"error": "No subscription Found."}, status=status.HTTP_404_NOT_FOUND
            )

        if not sub.razorpay_subscription_id:
            return Response(
                {"error": "No active Razorpay subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            razorpay.subscription.cancel(
                sub.razorpay_subscription_id, {"cancel_at_cycle_end": 1}
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "message": "Cancellation initiated. Access continues until the end of the current billing cycle."
            },
            status=status.HTTP_200_OK,
        )


class RazorpayWebhookApiView(APIView):
    """
    A singel endpoint thata handles all the webhook events from razorpay.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    handler_map = {
        "subscription.activated": handle_subscription_activated,
        "subscription.charged": handle_subscription_charged,
        "subscription.halted": handle_subscription_halted,
        "subscription.cancelled": handle_subscription_cancelled,
        "subscription.completed": handle_subscription_completed,
    }

    def post(self, request):
        # read payload first else drf prase will mess the bytes for signature verification

        webhook_body = request.body
        webhook_signature = request.headers.get("X-Razorpay-Signature", "")

        if not webhook_signature:
            return Response(
                {"error": "Missing signature header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            razorpay.utility.verify_webhook_signature(
                webhook_body.decode("utf-8"),
                webhook_signature,
                settings.RAZORPAY_WEBHOOK_SECRET,
            )
        except Exception:
            return Response(
                {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        event_id = request.headers.get("X-Razorpay-Event-Id", "")
        if event_id and RazorpayEvent.objects.filter(event_id=event_id).exists():
            return Response({"error": "Already processed."}, status=status.HTTP_200_OK)

        payload = json.loads(webhook_body)
        event_type = payload.get("event", "")
        subscription = (
            payload.get("payload", {}).get("subscription", {}).get("entity", {})
        )
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})

        PAYMENT_REQUIRED_EVENTS = {"subscription.activated", "subscription.charged"}

        handler = self.handler_map.get(event_type)
        if handler:
            if event_type in PAYMENT_REQUIRED_EVENTS:
                if subscription and payment:
                    handler(subscription, payment)
                # if payment missing, log it but return 200 — don't crash
            else:
                if subscription:
                    handler(subscription)

        if event_id:
            RazorpayEvent.objects.create(event_id=event_id, event_type=event_type)

        return Response({"status": "ok"})
