from datetime import datetime, UTC
from decimal import Decimal


from user.models import UserSubscription, SubscriptionPlan, UserSubscriptionHistory
from user.razorpay_client import client as razorpay

# helper


def _parse_unix_timestamp(timestamp):
    """ "
    unix the big watch
    converts to utc datetime object
    """
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, UTC)


def _get_sub(razorpay_id):
    """
    lookups to subscription by razorpay subscription id
    """
    try:
        return UserSubscription.objects.get(razorpay_subscription_id=razorpay_id)
    except UserSubscription.DoesNotExist:
        return None


def _convert_to_decimal(amount):
    """
    converts smallest currency unit to decimal
    """
    return Decimal(amount / Decimal(100))


def create_razorpay_subscription(user, plan_id):
    """
    request razorpay to create subscription for user with plan_id
    """

    plan = SubscriptionPlan.objects.get(id=plan_id)

    response = razorpay.subscription.create(
        {
            "plan_id": plan.razorpay_plan_id,
            "total_count": 90,
            "quantity": 1,
            "customer_notify": 1,
            "notes": {
                "user_id": str(user.id),
                "user_email": user.email,
                "plan_id": str(plan.id),
            },
        }
    )

    sub = user.subscription

    sub.razorpay_subscription_id = response["id"]
    sub.subscription_plan = plan
    sub.save(update_fields=["razorpay_subscription_id", "subscription_plan"])

    return {"subscription_id": response["id"], "status": response["status"]}


def handle_subscription_activated(subscription, payment):
    """
    on webhook subscription activated
    update the db for user subscription and create a payment history record
    """

    sub = _get_sub(subscription["id"])

    if not sub:
        return

    UserSubscriptionHistory.objects.create(
        user_subscription=sub,
        razorpay_payment_id=payment.get("id"),
        amount=_convert_to_decimal(payment.get("amount")),
        status=payment.get("status"),
    )

    sub.status = "active"
    sub.razorpay_status = subscription.get("status")
    sub.current_period_start = _parse_unix_timestamp(subscription.get("current_start"))
    sub.current_period_end = _parse_unix_timestamp(subscription.get("current_end"))
    sub.save(
        update_fields=[
            "status",
            "razorpay_status",
            "current_period_start",
            "current_period_end",
        ]
    )


def handle_subscription_charged(subscription, payment):
    """
    on webhook subscription charged
    update the db for user subscription and create a payment history record
    """

    sub = _get_sub(subscription["id"])

    if not sub:
        return

    UserSubscriptionHistory.objects.create(
        user_subscription=sub,
        razorpay_payment_id=payment.get("id"),
        amount=_convert_to_decimal(payment.get("amount")),
        status=payment.get("status"),
    )

    sub.status = "active"
    sub.razorpay_status = subscription.get("status")
    sub.current_period_start = _parse_unix_timestamp(subscription.get("current_start"))
    sub.current_period_end = _parse_unix_timestamp(subscription.get("current_end"))
    sub.save(
        update_fields=[
            "status",
            "razorpay_status",
            "current_period_start",
            "current_period_end",
        ]
    )


def handle_subscription_halted(subscription):
    """
    after 4 failed payments, subscription is halted.
    """

    sub = _get_sub(subscription["id"])

    if not sub:
        return

    sub.status = "expired"
    sub.razorpay_status = subscription.get("status")
    sub.save(update_fields=["status", "razorpay_status"])


def handle_subscription_cancelled(subscription):
    """
    subscription.cancelled
    either me from admin or user can cancel the subscription.
    access remains untill the end of current period.
    """

    sub = _get_sub(subscription["id"])

    if not sub:
        return

    sub.status = "cancelled"
    sub.razorpay_status = subscription.get("status")
    sub.save(update_fields=["status", "razorpay_status"])


def handle_subscription_completed(subscription):
    """
    subscription.completed
    subscription is completed after 120 payments.
    access remains untill the end of current period.
    """

    sub = _get_sub(subscription["id"])

    if not sub:
        return

    sub.status = "expired"
    sub.razorpay_status = subscription.get("status")
    sub.save(update_fields=["status", "razorpay_status"])
