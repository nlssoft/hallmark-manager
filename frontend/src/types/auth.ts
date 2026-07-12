import type { AxiosRequestConfig } from "axios";
import type { ReactNode } from "react";

export interface LoginRequest {
  username: string;
  password: string;
}

interface Profile {
  number: string;
  company_name: string;
  company_address: string;
  office_number1: string;
  office_number2: string;
  setting_mode: true;
  setting_reason: true;
}

interface SubscriptionPlan {
  tier: string;
  period: string;
  price: number;
  max_employees: number;
  max_services: number;
  max_assignments_per_customer: number;
  max_downloads: number;
}

interface Subscription {
  status: string;
  subscription_plan: SubscriptionPlan;
  current_period_start: string;
  current_period_end: string;
}

export interface User {
  public_id: string;
  username: string;
  email: string;
  profile: Profile;
  subscription: Subscription;
  is_parent: boolean;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isParent: boolean;
  loginUser: (data: LoginRequest) => Promise<void>;
}

export interface Props {
  children: ReactNode;
}

export interface RetryRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

export interface FailedQueueItem {
  resolve: (value?: unknown) => void;
  reject: (error: unknown) => void;
}
