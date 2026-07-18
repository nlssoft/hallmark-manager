import type { SubscriptionResponse } from "../types/backendTypes/apiAuth";
import type { Subscription } from "../types/frontedTypes/auth";
import { mapPlan } from "./plan";



export function mapSubscription(data: SubscriptionResponse): Subscription{
    return {
        status: data.status,
        Plan: mapPlan(data.plan),
        currentPeriodStart: data.current_period_start,
        currentPeriodEnd: data.current_period_start,
    }
}