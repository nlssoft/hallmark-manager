import type { PlanResponse } from "../types/backendTypes/apiAuth";
import type { Plan } from "../types/frontedTypes/auth";

export function mapPlan(data: PlanResponse | null): Plan | null{
    if (!data) {
        return null;
    }
    return {
        tier: data.tier,
        period: data.period,
        price: data.price,
        maxEmployees: data.max_employees,
        maxServices: data.max_services,
        maxAssignmentsPerCustomer: data.max_assignments_per_customer,
        maxDownloads: data.max_downloads
    }
}