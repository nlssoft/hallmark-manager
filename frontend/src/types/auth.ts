import type { AxiosRequestConfig } from "axios";
import type { ReactNode } from "react";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface User {
  public_id: string;
  username: string;
  email: string;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
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
