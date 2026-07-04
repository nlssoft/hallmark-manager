import json
import razorpay
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.permissions import ParentAccount_Only
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from user.models import Subscription, SubscriptionPlan, RazorpayEvent
from core.models import Customer

from user.Services.subscription_service import (
    create_razorpay_subscription,
    handle_subscription_activated,
    handle_subscription_charged,
    handle_subscription_halted,
    handle_subscription_cancelled,
    handle_subscription_completed,
)
from .razorpay_client import client as razorpay


def disable_employees():
    pass

def disable_services():
    pass

def removed_assigned_to():
    pass



class SubscriptionCreateApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def post(self, request):
        user = request.user

        new_plan_obj = request.data.get("new_plan_obj")
        plan_id = request.data.get("plan_id")
        disable_employee_ids = request.data.get("disable_employee")
        disable_service_ids = request.data.get("disable_service")
        remove_assigned_to_ids = request.data.get("remove_assigned_to")


        if not plan_id:
            return Response({"error": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        

        if user.subscription.tier == "gold":
            if user.employee.all().count() > new_plan_obj.max_employees:
                disable_employees(disable_employee_ids, new_plan_obj)

            if user.service.all().count() > new_plan_obj.max_services:
                disable_services(disable_service_ids, new_plan_obj)
            
            if (
                Customer.objects.filter(owner=user).annotate(
                    employee_count= Count("assigned_to")
                    .filter(employee_count__gt=new_plan_obj.max_assigned_toes)
                ).exists()
            ):
                removed_assigned_to(remove_assigned_to_ids, new_plan_obj)
         


        
        try:
            payment_data= create_razorpay_subscription(user, plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Plan does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        return Response(payment_data, status=status.HTTP_201_CREATED)
    

class SubscritionStatusApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def get(self, request):
        try:
            sub= request.user.subscription
        except Subscription.DoesNotExist:
            return Response({"error": "No subscription Found."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "status": sub.status,
            "tier": sub.tier,
            "subscription_id": sub.razorpay_subscription_id,
            "is_active": sub.is_active,
            "trial_end": sub.trial_end,
            "current_period_end": sub.current_period_end,
            "plan": {
                "tier": sub.subscription_plan.get_tier_display(),
                "period": sub.subscription_plan.get_period_display(),
                "price": str(sub.subscription_plan.price),
            } if sub.subscription_plan else None,
        }, status=status.HTTP_200_OK)


class SubscriptionCancelledApiView(APIView):
    permission_classes = [ParentAccount_Only]

    def post(self, request):
        
        try:
            sub= request.user.subscription
        except Subscription.DoesNotExist:
            return Response({"error": "No subscription Found."}, status=status.HTTP_404_NOT_FOUND)
        
        if not sub.razorpay_subscription_id:
            return Response(
                {"error": "No active Razorpay subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )
                
        try:
            razorpay.subscription.cancel(sub.razorpay_subscription_id, {"cancel_at_cycle_end": 1})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

        
        return Response({"message": "Cancellation initiated. Access continues until the end of the current billing cycle."}, status=status.HTTP_200_OK)
    

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

        webhook_body= request.body
        webhook_signature= request.headers.get("X-Razorpay-Signature", "")

        if not webhook_signature:
            return Response({"error": "Missing signature header"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            razorpay.utility.verify_webhook_signature(
                webhook_body.decode("utf-8"),
                webhook_signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception:
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
    
        event_id= request.headers.get("X-Razorpay-Event-Id", "")
        if event_id and RazorpayEvent.objects.filter(event_id=event_id).exists():
            return Response({"error": "Already processed."}, status=status.HTTP_200_OK)
        
        payload= json.loads(webhook_body)
        event_type= payload.get("event", "")
        subscription= (
            payload.get("payload", {})
            .get("subscription", {})
            .get("entity", {})
        )
        payment= (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        handler = self.handler_map.get(event_type)
        if handler and subscription and payment:
            handler(subscription, payment)
        elif handler and subscription:
            handler(subscription)
       
        
        if event_id:
            RazorpayEvent.objects.create(event_id=event_id, event_type=event_type)
        
        return Response({"status": "ok"})


