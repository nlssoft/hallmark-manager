export interface ProfileResponse {
  number: string;
  company_name: string;
  company_address: string;
  office_number1: string;
  office_number2: string;
  setting_mode: true;
  setting_reason: true;
}

export interface PlanResponse {
  tier: string;
  period: string;
  price: number;
  max_employees: number;
  max_services: number;
  max_assignments_per_customer: number;
  max_downloads: number;
}

export interface SubscriptionResponse {
  status: string;
  plan: PlanResponse | null;
  current_period_start: string;
  current_period_end: string;
}

export interface UserResponse {
  public_id: string;
  username: string;
  email: string;
  profile?: ProfileResponse | null;
  is_parent: boolean;
}