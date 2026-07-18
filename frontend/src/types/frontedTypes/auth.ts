import type { AxiosRequestConfig } from "axios";
import type { ReactNode } from "react";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Profile {
  number: string;
  companyName: string;
  companyAddress: string;
  officeNumber1: string;
  officeNumber2: string;
}

export interface Setting{
  owner: User
  imageRequierd: boolean;
  reasonRequierd: boolean;
}

export interface Plan {
  tier: string;
  period: string;
  price: number;
  maxEmployees: number;
  maxServices: number;
  maxAssignmentsPerCustomer: number;
  maxDownloads: number;
}

export interface Subscription {
  status: string;
  Plan: Plan | null;
  currentPeriodStart: string;
  currentPeriodEnd: string;
}

export interface User {
  publicId: string;
  username: string;
  email: string;
  profile?: Profile | null;
  isParent: boolean;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isParent: boolean;
  loginUser: (data: LoginRequest) => Promise<void>;
  logoutUser: () => Promise<void>;
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
