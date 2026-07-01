from datetime import datetime
from django.utils import timezone

from user.models import UserSubscription, RazorpayEvent
from user.razorpay_client import client as razorpay_client


def create_subscription(user, plan_id):
    